from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from dropship_import_mcp.job_store import FileJobStore
from dropship_import_mcp.provider import ImportProvider
from dropship_import_mcp.push_options import normalize_push_options
from dropship_import_mcp.resolver import resolve_source_url
from dropship_import_mcp.rules import apply_rules, normalize_rules


class ImportFlowService:
    def __init__(self, provider: ImportProvider, store: FileJobStore) -> None:
        self._provider = provider
        self._store = store

    async def get_rule_capabilities(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target_store = payload.get("target_store")
        provider_caps = await self._provider.get_rule_capabilities(target_store=target_store)
        return {
            "provider_label": provider_caps.get("provider_label", self._provider.name),
            "source_support": provider_caps.get("source_support", []),
            "stores": provider_caps.get("stores", []),
            "rule_families": provider_caps.get("rule_families", {}),
            "push_options": provider_caps.get("push_options", {}),
            "notes": provider_caps.get("notes", []),
        }

    async def validate_rules(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target_store = payload.get("target_store")
        rules = payload.get("rules") or {}
        provider_caps = await self._provider.get_rule_capabilities(target_store=target_store)
        validation = normalize_rules(rules, provider_caps.get("rule_families"))
        return {
            "provider_label": provider_caps.get("provider_label", self._provider.name),
            "target_store": target_store,
            "requested_rules": validation.get("requested_rules", {}),
            "effective_rules_snapshot": validation.get("effective_rules", {}),
            "warnings": validation.get("warnings", []),
            "errors": validation.get("errors", []),
        }

    async def prepare_import_candidate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        source_url = str(payload.get("source_url") or "").strip()
        if not source_url:
            raise ValueError("source_url is required")

        source_hint = str(payload.get("source_hint") or "auto").strip() or "auto"
        country = str(payload.get("country") or "US").strip() or "US"
        visibility_mode = str(payload.get("visibility_mode") or "backend_only").strip() or "backend_only"
        target_store = payload.get("target_store")
        rules = payload.get("rules") or {}

        provider_caps = await self._provider.get_rule_capabilities(target_store=target_store)
        validated_rules = normalize_rules(rules, provider_caps.get("rule_families"))
        if validated_rules.get("errors"):
            raise ValueError("; ".join(validated_rules["errors"]))

        resolved = await resolve_source_url(source_url, source_hint)
        prepared = await self._provider.prepare_candidate(
            source_url=resolved["resolved_url"],
            source_hint=resolved["source_hint"],
            country=country,
        )

        original_draft = deepcopy(prepared["draft"])
        effective_rules = validated_rules.get("effective_rules", {})
        ruled = apply_rules(prepared["draft"], effective_rules)
        final_draft = ruled["draft"]

        job = {
            "status": "preview_ready",
            "created_at": _utc_now(),
            "provider_label": prepared.get("provider_label", self._provider.name),
            "source_url": source_url,
            "resolved_source_url": resolved["resolved_url"],
            "source_hint": resolved["source_hint"],
            "resolver_mode": resolved.get("resolver_mode"),
            "country": country,
            "target_store": target_store,
            "visibility_mode": visibility_mode,
            "requested_rules": validated_rules.get("requested_rules", {}),
            "effective_rules_snapshot": effective_rules,
            "rules": effective_rules,
            "provider_state": prepared["provider_state"],
            "original_draft": original_draft,
            "draft": final_draft,
            "warnings": list(resolved.get("warnings") or [])
            + list(prepared.get("warnings") or [])
            + list(validated_rules.get("warnings") or [])
            + list((ruled.get("summary") or {}).get("warnings") or []),
            "rule_summary": ruled.get("summary") or {},
        }
        job_id = self._store.create(job)
        job["job_id"] = job_id
        self._store.save(job_id, job)
        return self._preview(job)

    async def get_import_preview(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        job_id = str(payload.get("job_id") or "").strip()
        if not job_id:
            raise ValueError("job_id is required")
        job = self._store.load(job_id)
        return self._preview(job)

    async def set_product_visibility(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        job_id = str(payload.get("job_id") or "").strip()
        visibility_mode = str(payload.get("visibility_mode") or "").strip()
        if not job_id or not visibility_mode:
            raise ValueError("job_id and visibility_mode are required")
        job = self._store.load(job_id)
        job["visibility_mode"] = visibility_mode
        job["updated_at"] = _utc_now()
        self._store.save(job_id, job)
        return {
            "job_id": job_id,
            "status": job.get("status"),
            "visibility_mode": visibility_mode,
        }

    async def confirm_push_to_store(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        job_id = str(payload.get("job_id") or "").strip()
        if not job_id:
            raise ValueError("job_id is required")

        job = self._store.load(job_id)
        target_store = payload.get("target_store") or job.get("target_store")
        visibility_mode = payload.get("visibility_mode") or job.get("visibility_mode") or "backend_only"
        provider_caps = await self._provider.get_rule_capabilities(target_store=target_store)
        push_option_check = normalize_push_options(
            payload.get("push_options"),
            visibility_mode,
            provider_caps.get("push_options"),
        )
        if push_option_check.get("errors"):
            raise ValueError("; ".join(push_option_check["errors"]))
        effective_push_options = push_option_check.get("effective_push_options", {})

        result = await self._provider.commit_candidate(
            provider_state=job["provider_state"],
            draft=job["draft"],
            target_store=target_store,
            visibility_mode=visibility_mode,
            push_options=effective_push_options,
        )
        job["status"] = result.get("job_status", "push_requested")
        job["updated_at"] = _utc_now()
        job["target_store"] = target_store
        job["visibility_mode"] = visibility_mode
        job["requested_push_options"] = push_option_check.get("requested_push_options", {})
        job["effective_push_options"] = effective_push_options
        job["push_option_warnings"] = push_option_check.get("warnings", [])
        job["push_result"] = result
        self._store.save(job_id, job)

        return {
            "job_id": job_id,
            "status": job["status"],
            "target_store": target_store,
            "visibility_requested": visibility_mode,
            "visibility_applied": result.get("visibility_applied", visibility_mode),
            "push_options_applied": result.get("push_options_applied", effective_push_options),
            "job_summary": result.get("summary", {}),
            "warnings": list(push_option_check.get("warnings") or []) + list(result.get("warnings", [])),
        }

    async def get_job_status(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        job_id = str(payload.get("job_id") or "").strip()
        if not job_id:
            raise ValueError("job_id is required")
        job = self._store.load(job_id)
        return {
            "job_id": job_id,
            "status": job.get("status"),
            "created_at": job.get("created_at"),
            "updated_at": job.get("updated_at"),
            "target_store": job.get("target_store"),
            "visibility_mode": job.get("visibility_mode"),
            "warnings": list(job.get("warnings", [])) + list(job.get("push_option_warnings", [])),
            "has_push_result": bool(job.get("push_result")),
        }

    def _preview(self, job: Dict[str, Any]) -> Dict[str, Any]:
        original = job["original_draft"]
        final = job["draft"]
        preview = {
            "job_id": job.get("job_id"),
            "status": job.get("status"),
            "source_url": job.get("source_url"),
            "resolved_source_url": job.get("resolved_source_url"),
            "resolver_mode": job.get("resolver_mode"),
            "target_store": job.get("target_store"),
            "visibility_mode": job.get("visibility_mode"),
            "title_before": original.get("title"),
            "title_after": final.get("title"),
            "description_changed": (original.get("description_html") or "") != (final.get("description_html") or ""),
            "images_before": len(original.get("images") or []),
            "images_after": len(final.get("images") or []),
            "variant_count": len(final.get("variants") or []),
            "price_range_before": _price_range(original),
            "price_range_after": _price_range(final),
            "tags_before": original.get("tags") or [],
            "tags_after": final.get("tags") or [],
            "requested_rules": job.get("requested_rules", {}),
            "effective_rules_snapshot": job.get("effective_rules_snapshot", {}),
            "rule_summary": job.get("rule_summary", {}),
            "warnings": job.get("warnings", []),
        }
        if final.get("variants"):
            preview["variant_preview"] = [
                {
                    "title": item.get("title"),
                    "supplier_price": item.get("supplier_price"),
                    "offer_price": item.get("offer_price"),
                    "sku": item.get("sku"),
                }
                for item in final.get("variants")[:5]
            ]
        return preview


def _price_range(draft: Dict[str, Any]) -> Dict[str, Optional[float]]:
    prices = []
    for variant in draft.get("variants") or []:
        for key in ("offer_price", "supplier_price"):
            value = variant.get(key)
            if value is None:
                continue
            try:
                prices.append(float(value))
                break
            except (TypeError, ValueError):
                continue
    if not prices:
        return {"min": None, "max": None}
    return {"min": min(prices), "max": max(prices)}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
