from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional, Set

_KNOWN_TOP_LEVEL_RULE_KEYS = {"pricing", "content", "images", "instruction_text"}
_KNOWN_PRICING_KEYS = {"mode", "multiplier", "fixed_markup", "round_digits"}
_KNOWN_CONTENT_KEYS = {
    "title_override",
    "title_prefix",
    "title_suffix",
    "description_override_html",
    "description_append_html",
    "tags_add",
}
_KNOWN_IMAGE_KEYS = {"keep_first_n", "drop_indexes", "translate_image_text", "remove_logo"}
_DEFAULT_PRICING_MODES = {"provider_default", "multiplier", "fixed_markup"}


def normalize_rules(rules: Dict[str, Any], rule_capabilities: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    requested_rules = deepcopy(rules or {})
    warnings: List[str] = []
    errors: List[str] = []
    effective_rules: Dict[str, Any] = {}

    if requested_rules and not isinstance(requested_rules, dict):
        return {
            "requested_rules": requested_rules,
            "effective_rules": {},
            "warnings": [],
            "errors": ["rules must be an object"],
        }

    requested_rules = requested_rules if isinstance(requested_rules, dict) else {}
    rule_capabilities = rule_capabilities or {}

    for key in sorted(requested_rules):
        if key not in _KNOWN_TOP_LEVEL_RULE_KEYS:
            warnings.append(f"Unknown top-level rule key '{key}' was ignored.")

    pricing = _normalize_pricing_rules(requested_rules.get("pricing"), rule_capabilities.get("pricing"), warnings, errors)
    if pricing:
        effective_rules["pricing"] = pricing

    content = _normalize_content_rules(requested_rules.get("content"), rule_capabilities.get("content"), warnings, errors)
    if content:
        effective_rules["content"] = content

    images = _normalize_image_rules(requested_rules.get("images"), rule_capabilities.get("images"), warnings, errors)
    if images:
        effective_rules["images"] = images

    instruction_text = requested_rules.get("instruction_text")
    if instruction_text not in (None, ""):
        if isinstance(instruction_text, str):
            effective_rules["instruction_text"] = instruction_text
            warnings.append(
                "instruction_text is stored in the rule snapshot for operator context, but only structured rules are applied automatically."
            )
        else:
            errors.append("instruction_text must be a string when provided.")

    return {
        "requested_rules": requested_rules,
        "effective_rules": effective_rules,
        "warnings": warnings,
        "errors": errors,
    }


def apply_rules(draft: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    draft = deepcopy(draft)
    summary: Dict[str, Any] = {"applied": [], "warnings": []}

    pricing = rules.get("pricing") or {}
    if pricing:
        _apply_pricing_rules(draft, pricing, summary)

    content = rules.get("content") or {}
    if content:
        _apply_content_rules(draft, content, summary)

    images = rules.get("images") or {}
    if images:
        _apply_image_rules(draft, images, summary)

    instruction_text = rules.get("instruction_text")
    if instruction_text:
        summary["warnings"].append(
            "Freeform instruction_text is recorded for operator context, but only structured rules are applied automatically in this MVP."
        )

    return {"draft": draft, "summary": summary}


def _normalize_pricing_rules(
    pricing: Any,
    capability: Optional[Dict[str, Any]],
    warnings: List[str],
    errors: List[str],
) -> Dict[str, Any]:
    if pricing in (None, {}):
        return {}
    if not isinstance(pricing, dict):
        errors.append("pricing must be an object when provided.")
        return {}

    capability = capability or {}
    if capability.get("supported") is False:
        warnings.append("Pricing rules were ignored because the current provider does not support pricing edits.")
        return {}

    mode = str(pricing.get("mode") or "provider_default")
    if mode not in _DEFAULT_PRICING_MODES:
        errors.append(f"Unsupported pricing.mode '{mode}'.")
        return {}

    allowed_modes = set(capability.get("modes") or _DEFAULT_PRICING_MODES)
    if mode not in allowed_modes:
        warnings.append(f"Pricing mode '{mode}' is not supported by the current provider and was ignored.")
        return {}

    for key in sorted(pricing):
        if key not in _KNOWN_PRICING_KEYS:
            warnings.append(f"Unknown pricing rule key '{key}' was ignored.")

    normalized: Dict[str, Any] = {"mode": mode}
    if mode == "multiplier":
        multiplier = _as_float(pricing.get("multiplier"), None)
        if multiplier is None:
            errors.append("pricing.multiplier must be a number when pricing.mode='multiplier'.")
            return {}
        normalized["multiplier"] = multiplier
    elif mode == "fixed_markup":
        markup = _as_float(pricing.get("fixed_markup"), None)
        if markup is None:
            errors.append("pricing.fixed_markup must be a number when pricing.mode='fixed_markup'.")
            return {}
        normalized["fixed_markup"] = markup

    if mode != "provider_default":
        round_digits = pricing.get("round_digits", 2)
        try:
            normalized["round_digits"] = int(round_digits)
        except (TypeError, ValueError):
            errors.append("pricing.round_digits must be an integer when provided.")
            return {}

    return normalized


def _normalize_content_rules(
    content: Any,
    capability: Optional[Dict[str, Any]],
    warnings: List[str],
    errors: List[str],
) -> Dict[str, Any]:
    if content in (None, {}):
        return {}
    if not isinstance(content, dict):
        errors.append("content must be an object when provided.")
        return {}

    allowed_keys = _allowed_rule_keys(capability, _KNOWN_CONTENT_KEYS)
    normalized: Dict[str, Any] = {}
    for key in sorted(content):
        if key not in _KNOWN_CONTENT_KEYS:
            warnings.append(f"Unknown content rule key '{key}' was ignored.")
            continue
        if key not in allowed_keys:
            warnings.append(f"Content rule '{key}' is not supported by the current provider and was ignored.")
            continue
        value = content.get(key)
        if key == "tags_add":
            if value in (None, []):
                continue
            if not isinstance(value, list):
                errors.append("content.tags_add must be an array of strings when provided.")
                continue
            tags = []
            for raw_tag in value:
                tag = str(raw_tag).strip()
                if tag and tag not in tags:
                    tags.append(tag)
            if tags:
                normalized[key] = tags
            continue
        if value in (None, ""):
            continue
        normalized[key] = str(value)

    return normalized


def _normalize_image_rules(
    images: Any,
    capability: Optional[Dict[str, Any]],
    warnings: List[str],
    errors: List[str],
) -> Dict[str, Any]:
    if images in (None, {}):
        return {}
    if not isinstance(images, dict):
        errors.append("images must be an object when provided.")
        return {}

    allowed_keys = _allowed_rule_keys(capability, _KNOWN_IMAGE_KEYS)
    normalized: Dict[str, Any] = {}
    for key in sorted(images):
        if key not in _KNOWN_IMAGE_KEYS:
            warnings.append(f"Unknown image rule key '{key}' was ignored.")
            continue
        if key not in allowed_keys:
            warnings.append(f"Image rule '{key}' is not supported by the current provider and was ignored.")
            continue

        value = images.get(key)
        if key == "keep_first_n":
            if value is None:
                continue
            try:
                keep_first_n = int(value)
            except (TypeError, ValueError):
                errors.append("images.keep_first_n must be an integer when provided.")
                continue
            if keep_first_n < 0:
                errors.append("images.keep_first_n must be >= 0.")
                continue
            normalized[key] = keep_first_n
            continue

        if key == "drop_indexes":
            if value in (None, []):
                continue
            if not isinstance(value, list):
                errors.append("images.drop_indexes must be an array of integers when provided.")
                continue
            indexes = []
            for raw_index in value:
                try:
                    index = int(raw_index)
                except (TypeError, ValueError):
                    errors.append("images.drop_indexes must contain only integers.")
                    indexes = []
                    break
                if index >= 0 and index not in indexes:
                    indexes.append(index)
            if indexes:
                normalized[key] = sorted(indexes)
            continue

        normalized[key] = bool(value)

    return normalized


def _apply_pricing_rules(draft: Dict[str, Any], pricing: Dict[str, Any], summary: Dict[str, Any]) -> None:
    mode = pricing.get("mode", "provider_default")
    if mode == "provider_default":
        return

    multiplier = _as_float(pricing.get("multiplier"), 1.0)
    markup = _as_float(pricing.get("fixed_markup"), 0.0)
    round_digits = int(pricing.get("round_digits", 2))

    variants = draft.get("variants") or []
    changed = 0
    for variant in variants:
        base = _first_price(variant)
        if base is None:
            continue
        if mode == "multiplier":
            new_price = round(base * multiplier, round_digits)
        elif mode == "fixed_markup":
            new_price = round(base + markup, round_digits)
        else:
            summary["warnings"].append(f"Unsupported pricing mode '{mode}' was ignored.")
            return
        variant["offer_price"] = new_price
        changed += 1

    summary["applied"].append({"rule_family": "pricing", "mode": mode, "variants_changed": changed})


def _apply_content_rules(draft: Dict[str, Any], content: Dict[str, Any], summary: Dict[str, Any]) -> None:
    title = draft.get("title") or ""
    if content.get("title_override"):
        title = str(content["title_override"]).strip()
    if content.get("title_prefix"):
        title = str(content["title_prefix"]) + title
    if content.get("title_suffix"):
        title = title + str(content["title_suffix"])
    if title:
        draft["title"] = title

    if content.get("description_override_html"):
        draft["description_html"] = str(content["description_override_html"])
    elif content.get("description_append_html"):
        existing = draft.get("description_html") or ""
        draft["description_html"] = existing + str(content["description_append_html"])

    if content.get("tags_add"):
        existing_tags = list(draft.get("tags") or [])
        for tag in content.get("tags_add") or []:
            if tag not in existing_tags:
                existing_tags.append(tag)
        draft["tags"] = existing_tags

    summary["applied"].append({"rule_family": "content"})


def _apply_image_rules(draft: Dict[str, Any], images: Dict[str, Any], summary: Dict[str, Any]) -> None:
    image_list = list(draft.get("images") or [])
    original_count = len(image_list)

    drop_indexes = sorted(set(images.get("drop_indexes") or []), reverse=True)
    for idx in drop_indexes:
        if 0 <= idx < len(image_list):
            image_list.pop(idx)

    keep_first_n = images.get("keep_first_n")
    if keep_first_n is not None:
        image_list = image_list[: int(keep_first_n)]

    if images.get("translate_image_text"):
        summary["warnings"].append("translate_image_text is not auto-applied in this MVP.")
    if images.get("remove_logo"):
        summary["warnings"].append("remove_logo is not auto-applied in this MVP.")

    draft["images"] = image_list
    summary["applied"].append(
        {"rule_family": "images", "image_count_before": original_count, "image_count_after": len(image_list)}
    )


def _first_price(variant: Dict[str, Any]) -> Any:
    for key in ("offer_price", "supplier_price"):
        value = variant.get(key)
        parsed = _as_float(value, None)
        if parsed is not None:
            return parsed
    return None


def _as_float(value: Any, default: Any) -> Any:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _allowed_rule_keys(capability: Optional[Dict[str, Any]], default_keys: Set[str]) -> Set[str]:
    capability = capability or {}
    supported = capability.get("supported")
    unsupported = {str(item) for item in capability.get("unsupported") or []}

    if isinstance(supported, list):
        allowed = {str(item) for item in supported}
    elif supported is False:
        allowed = set()
    else:
        allowed = set(default_keys)

    return allowed - unsupported
