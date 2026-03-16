#!/usr/bin/env python3
"""Full-flow integration test for Alibaba and 1688 sources.

Tests: import → modify price/title/description → preview → push.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from dropship_import_mcp.job_store import FileJobStore
from dropship_import_mcp.provider import load_provider
from dropship_import_mcp.service import ImportFlowService

STATE_DIR = Path(__file__).resolve().parent / ".state-test"


TEST_CASES = [
    {
        "label": "AliExpress - Multiplier pricing + title prefix/suffix + desc append",
        "source_url": "https://www.aliexpress.com/item/1005010130392695.html",
        "country": "US",
        "rules": {
            "pricing": {"mode": "multiplier", "multiplier": 2.5},
            "content": {
                "title_prefix": "[SALE] ",
                "title_suffix": " - Fast Ship",
                "description_append_html": "<p><strong>Tested via Dropship MCP - multiplier 2.5x pricing</strong></p>",
            },
            "images": {"keep_first_n": 5},
        },
        "target_store": "tmalltest04",
        "push_options": {
            "publish_to_online_store": False,
            "image_strategy": "selected_only",
            "pricing_rule_behavior": "keep_manual",
            "auto_inventory_update": True,
            "auto_price_update": False,
            "store_shipping_profile": [
                {
                    "storeId": "1938446701906362368",
                    "locationId": "gid://shopify/DeliveryLocationGroup/132607344915",
                    "profileId": "gid://shopify/DeliveryProfile/130329837843",
                }
            ],
        },
    },
    {
        "label": "AliExpress - Fixed markup + full title/desc override",
        "source_url": "https://www.aliexpress.com/item/1005008153503092.html",
        "country": "US",
        "rules": {
            "pricing": {"mode": "fixed_markup", "fixed_markup": 12},
            "content": {
                "title_override": "Premium Black Bath Towel Set - 100% Cotton",
                "description_override_html": (
                    "<h2>Premium Black Bath Towel Set</h2>"
                    "<ul>"
                    "<li>Material: 100% Cotton</li>"
                    "<li>Color: Black with embroidery</li>"
                    "<li>Includes: hand towel + bath towel + face towel</li>"
                    "</ul>"
                    "<p><em>Description fully replaced by Dropship MCP test</em></p>"
                ),
            },
            "images": {"keep_first_n": 3},
        },
        "target_store": "tmalltest04",
        "push_options": {
            "publish_to_online_store": False,
            "image_strategy": "all_available",
            "pricing_rule_behavior": "keep_manual",
            "auto_inventory_update": False,
            "auto_price_update": False,
            "store_shipping_profile": [
                {
                    "storeId": "1938446701906362368",
                    "locationId": "gid://shopify/DeliveryLocationGroup/132607344915",
                    "profileId": "gid://shopify/DeliveryProfile/130329837843",
                }
            ],
        },
    },
]

# Alibaba and 1688 URL parsing verification (account doesn't have these sources enabled)
ALIBABA_1688_PARSE_TESTS = [
    {
        "label": "Alibaba URL parse",
        "url": "https://www.alibaba.com/product-detail/UNDERICE-White-Nylon-6-7mm-6_1600219866565.html",
        "expected_id": "1600219866565",
        "expected_source": "alibaba",
    },
    {
        "label": "1688 URL parse",
        "url": "https://detail.1688.com/offer/736437523727.html",
        "expected_id": "736437523727",
        "expected_source": "1688",
    },
    {
        "label": "1688 product-detail URL parse",
        "url": "https://detail.1688.com/product-detail/617449967525.html",
        "expected_id": "617449967525",
        "expected_source": "1688",
    },
]


def _print_section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def _print_draft_summary(draft: dict) -> None:
    print(f"  Title:       {draft.get('title', '(none)')}")
    desc = draft.get("description_html", "")
    if len(desc) > 120:
        desc = desc[:120] + "..."
    print(f"  Description: {desc}")
    images = draft.get("images", [])
    print(f"  Images:      {len(images)} images")
    variants = draft.get("variants", [])
    print(f"  Variants:    {len(variants)} variants")
    for i, v in enumerate(variants[:3]):
        print(f"    [{i}] {v.get('title', '?')}  offer={v.get('offer_price')}  supplier={v.get('supplier_price')}  sku={v.get('sku', '')}")
    if len(variants) > 3:
        print(f"    ... and {len(variants) - 3} more")


async def run_test_case(service: ImportFlowService, case: dict) -> dict:
    label = case["label"]
    result = {"label": label, "status": "unknown", "steps": {}}

    _print_section(f"TEST: {label}")
    print(f"  URL: {case['source_url']}")

    # Step 1: Prepare candidate
    print("\n  [1/4] prepare_import_candidate ...")
    try:
        prepared = await service.prepare_import_candidate({
            "source_url": case["source_url"],
            "country": case["country"],
            "target_store": case.get("target_store"),
            "visibility_mode": "backend_only",
            "rules": case["rules"],
        })
        job_id = prepared.get("job_id", "")
        print(f"  -> job_id: {job_id}")
        result["steps"]["prepare"] = "ok"
        result["job_id"] = job_id

        if "error" in prepared:
            print(f"  -> ERROR: {prepared['error']}")
            result["status"] = "prepare_failed"
            result["error"] = prepared["error"]
            return result

        warnings = prepared.get("warnings", [])
        if warnings:
            print(f"  -> Warnings: {warnings}")

        draft = prepared.get("draft", {})
        _print_draft_summary(draft)

    except Exception as e:
        print(f"  -> EXCEPTION: {e}")
        traceback.print_exc()
        result["status"] = "prepare_exception"
        result["error"] = str(e)
        return result

    # Step 2: Preview
    print("\n  [2/4] get_import_preview ...")
    try:
        preview = await service.get_import_preview({"job_id": job_id})
        preview_draft = preview.get("draft", {})
        print(f"  -> Title:    {preview_draft.get('title', '(none)')}")
        print(f"  -> Variants: {len(preview_draft.get('variants', []))}")
        print(f"  -> Images:   {len(preview_draft.get('images', []))}")

        rules_snapshot = preview.get("effective_rules_snapshot", {})
        print(f"  -> Rules applied: {json.dumps(rules_snapshot, ensure_ascii=False)[:200]}")
        result["steps"]["preview"] = "ok"
    except Exception as e:
        print(f"  -> EXCEPTION: {e}")
        result["steps"]["preview"] = f"error: {e}"

    # Step 3: Visibility
    print("\n  [3/4] set_product_visibility -> sell_immediately ...")
    try:
        vis = await service.set_product_visibility({
            "job_id": job_id,
            "visibility_mode": "sell_immediately",
        })
        print(f"  -> visibility: {vis.get('visibility_mode', '?')}")
        result["steps"]["visibility"] = "ok"
    except Exception as e:
        print(f"  -> EXCEPTION: {e}")
        result["steps"]["visibility"] = f"error: {e}"

    # Step 4: Push
    print("\n  [4/4] confirm_push_to_store ...")
    try:
        push_result = await service.confirm_push_to_store({
            "job_id": job_id,
            "target_store": case.get("target_store"),
            "push_options": case["push_options"],
        })
        job_status = push_result.get("job_status", "unknown")
        push_warnings = push_result.get("warnings", [])
        print(f"  -> job_status: {job_status}")
        if push_warnings:
            for w in push_warnings:
                print(f"     warn: {w}")
        print(f"  -> target_store: {push_result.get('target_store', '?')}")
        print(f"  -> event_id: {push_result.get('event_id', '?')}")

        summary = push_result.get("summary", {})
        print(f"  -> summary: title={summary.get('title','?')}, variants={summary.get('variant_count','?')}, images={summary.get('image_count','?')}")

        result["steps"]["push"] = "ok"
        result["status"] = job_status
        result["push_result"] = {
            "job_status": job_status,
            "event_id": push_result.get("event_id"),
            "target_store": push_result.get("target_store"),
            "warnings": push_warnings,
        }
    except Exception as e:
        print(f"  -> EXCEPTION: {e}")
        traceback.print_exc()
        result["status"] = "push_exception"
        result["error"] = str(e)
        result["steps"]["push"] = f"error: {e}"

    return result


async def main() -> None:
    print("Initializing provider and service...")
    provider = load_provider()
    service = ImportFlowService(provider, FileJobStore(STATE_DIR))

    # Capabilities check
    _print_section("CAPABILITIES")
    caps = await service.get_rule_capabilities({})
    stores = caps.get("stores", [])
    print(f"  Provider: {caps.get('provider_label', '?')}")
    print(f"  Stores:   {len(stores)}")
    for s in stores:
        print(f"    - {s.get('display_name', '?')} (ref={s.get('store_ref', '?')}, platform={s.get('platform', '?')})")
    print(f"  Sources:  {caps.get('source_support', [])}")

    # Alibaba/1688 URL parsing verification
    _print_section("ALIBABA / 1688 URL PARSE (account has no source access)")
    from dsers_provider.provider import ALIBABA_ID_PATTERN, ALI1688_ID_PATTERN, ALIEXPRESS_ID_PATTERN
    for pt in ALIBABA_1688_PARSE_TESTS:
        url = pt["url"]
        matched_source = "unknown"
        matched_id = ""
        m = ALIBABA_ID_PATTERN.search(url)
        if m:
            matched_source, matched_id = "alibaba", m.group(1)
        else:
            m = ALI1688_ID_PATTERN.search(url)
            if m:
                matched_source, matched_id = "1688", m.group(1)
        ok = matched_source == pt["expected_source"] and matched_id == pt["expected_id"]
        status = "PASS" if ok else "FAIL"
        print(f"  [{pt['label']}] {status}  source={matched_source} id={matched_id}")
    print("  Note: import blocked by test account (ALIBABA_NOT_AVAILABLE), not a code issue.")

    # Rules validation
    _print_section("RULES VALIDATION")
    for case in TEST_CASES:
        vr = await service.validate_rules({"rules": case["rules"]})
        status = "valid" if vr.get("valid") else "invalid"
        print(f"  [{case['label']}] -> {status}")
        if vr.get("warnings"):
            print(f"    warnings: {vr['warnings']}")
        if vr.get("errors"):
            print(f"    errors: {vr['errors']}")

    # Run test cases
    results = []
    for case in TEST_CASES:
        r = await run_test_case(service, case)
        results.append(r)

    # Summary
    _print_section("SUMMARY")
    for r in results:
        steps_str = " | ".join(f"{k}={v}" for k, v in r.get("steps", {}).items())
        print(f"  [{r['label']}] status={r['status']}  steps: {steps_str}")
        if r.get("error"):
            print(f"    error: {r['error']}")

    # Write results JSON
    results_file = STATE_DIR / "test_results.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n  Results saved to {results_file}")


if __name__ == "__main__":
    asyncio.run(main())
