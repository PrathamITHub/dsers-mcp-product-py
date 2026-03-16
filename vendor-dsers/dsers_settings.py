"""DSers Settings module — MCP tools for dsers-settings-bff, dsers-pay-bff, and dsers-plan-bff APIs."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from mcp.types import TextContent, Tool

if TYPE_CHECKING:
    from dsers_mcp_base.client import DSersClient


def register(app: Any, client: "DSersClient") -> tuple[list[Tool], Any]:
    """Register all settings-related MCP tools. Returns (TOOLS, handle)."""

    TOOLS = [
        # --- Global Settings (infra-setting-bff / dsers-settings-bff) ---
        Tool(
            name="dsers_get_global_settings",
            description="Get global infrastructure settings (infra-setting-bff). Returns list of setting entries.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="dsers_get_pricing_rules",
            description="Get product pricing rules for a store. Requires storeId.",
            inputSchema={
                "type": "object",
                "properties": {
                    "storeId": {"type": "string", "description": "Store ID to fetch pricing rules for"},
                },
                "required": ["storeId"],
            },
        ),
        Tool(
            name="dsers_update_pricing_rule",
            description="Update product pricing rule configuration. Pass rule config in body.",
            inputSchema={
                "type": "object",
                "properties": {
                    "rule": {
                        "type": "object",
                        "description": "Pricing rule configuration object",
                    },
                },
                "required": ["rule"],
            },
        ),
        Tool(
            name="dsers_get_auto_sync_price",
            description="Get auto-sync price settings for products.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="dsers_update_auto_sync_price",
            description="Update auto-sync price settings. Pass settings object in body.",
            inputSchema={
                "type": "object",
                "properties": {
                    "settings": {
                        "type": "object",
                        "description": "Auto-sync price settings to apply",
                    },
                },
                "required": ["settings"],
            },
        ),
        Tool(
            name="dsers_get_automated_mapping",
            description="Get automated product mapping settings.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="dsers_update_automated_mapping",
            description="Update automated product mapping settings. Pass settings object in body.",
            inputSchema={
                "type": "object",
                "properties": {
                    "settings": {
                        "type": "object",
                        "description": "Automated mapping settings to apply",
                    },
                },
                "required": ["settings"],
            },
        ),
        Tool(
            name="dsers_get_product_shipping_info",
            description="Get user shipping template info for a supplier app.",
            inputSchema={
                "type": "object",
                "properties": {
                    "supplierAppId": {
                        "type": "integer",
                        "description": "Supplier app ID",
                    },
                },
                "required": ["supplierAppId"],
            },
        ),
        Tool(
            name="dsers_update_product_shipping_info",
            description="Update user shipping template info for a supplier app.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "boolean",
                        "description": "Whether the shipping configuration is enabled",
                    },
                    "shippingInfo": {
                        "type": "object",
                        "description": "ShippingInfo object from GET /product/shipping/get",
                    },
                },
                "required": ["shippingInfo"],
            },
        ),
        Tool(
            name="dsers_get_product_ship_settings",
            description="Get per-product shipping settings for supplier products.",
            inputSchema={
                "type": "object",
                "properties": {
                    "supplierProductId": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Supplier product IDs",
                    },
                    "supplierAppId": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Supplier app IDs",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="dsers_get_shipping_addresses",
            description="Get paginated list of shipping addresses.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "Page number (1-based)"},
                    "pageSize": {"type": "integer", "description": "Number of items per page"},
                },
                "required": [],
            },
        ),
        Tool(
            name="dsers_add_shipping_address",
            description="Add a new shipping address. Pass address object in body.",
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "object",
                        "description": "Shipping address (name, country, address, phone, etc.)",
                    },
                },
                "required": ["address"],
            },
        ),
        Tool(
            name="dsers_get_phone_list",
            description="Get list of phone numbers for orders.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        # --- Billing (dsers-pay-bff) ---
        Tool(
            name="dsers_get_bill_list",
            description="Get paginated list of bills/invoices.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "Page number (1-based)"},
                    "pageSize": {"type": "integer", "description": "Number of items per page"},
                },
                "required": [],
            },
        ),
        Tool(
            name="dsers_get_bill_detail",
            description="Get detail of a specific bill by billId.",
            inputSchema={
                "type": "object",
                "properties": {
                    "billId": {"type": "string", "description": "Bill ID to fetch"},
                },
                "required": ["billId"],
            },
        ),
        Tool(
            name="dsers_get_payment_methods",
            description="Get available payment methods.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        # --- Subscription Plan (dsers-plan-bff) ---
        Tool(
            name="dsers_get_current_plan",
            description="Get current subscription plan.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="dsers_get_plan_limits",
            description="Get plan usage limits and quotas.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="dsers_get_all_plans",
            description="Get all plan types and their limits.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]

    def reply(data: Any) -> list[TextContent]:
        return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]

    async def handle(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        try:
            # --- Global Settings ---
            if name == "dsers_get_global_settings":
                data = await client.get("/infra-setting-bff/setting/list")
                return reply(data)

            if name == "dsers_get_pricing_rules":
                store_id = arguments.get("storeId")
                if not store_id:
                    return reply({"error": "storeId is required"})
                data = await client.get("/dsers-settings-bff/product/pricing-rule", storeId=store_id)
                return reply(data)

            if name == "dsers_update_pricing_rule":
                rule = arguments.get("rule")
                if rule is None:
                    return reply({"error": "rule is required"})
                data = await client.put("/dsers-settings-bff/product/pricing-rule", json=rule)
                return reply(data)

            if name == "dsers_get_auto_sync_price":
                data = await client.get("/dsers-settings-bff/product/auto-sync-price")
                return reply(data)

            if name == "dsers_update_auto_sync_price":
                settings = arguments.get("settings")
                if settings is None:
                    return reply({"error": "settings is required"})
                data = await client.put("/dsers-settings-bff/product/auto-sync-price", json=settings)
                return reply(data)

            if name == "dsers_get_automated_mapping":
                data = await client.get("/dsers-settings-bff/product/automated-mapping")
                return reply(data)

            if name == "dsers_update_automated_mapping":
                settings = arguments.get("settings")
                if settings is None:
                    return reply({"error": "settings is required"})
                data = await client.put("/dsers-settings-bff/product/automated-mapping", json=settings)
                return reply(data)

            if name == "dsers_get_product_shipping_info":
                supplier_app_id = arguments.get("supplierAppId")
                if supplier_app_id is None:
                    return reply({"error": "supplierAppId is required"})
                data = await client.get("/dsers-settings-bff/product/shipping/get", supplierAppId=supplier_app_id)
                return reply(data)

            if name == "dsers_update_product_shipping_info":
                shipping_info = arguments.get("shippingInfo")
                if shipping_info is None:
                    return reply({"error": "shippingInfo is required"})
                body = {"shippingInfo": shipping_info}
                if "status" in arguments:
                    body["status"] = arguments.get("status")
                data = await client.put("/dsers-settings-bff/product/shipping/update", json=body)
                return reply(data)

            if name == "dsers_get_product_ship_settings":
                params = {}
                if arguments.get("supplierProductId") is not None:
                    params["supplierProductId"] = arguments.get("supplierProductId")
                if arguments.get("supplierAppId") is not None:
                    params["supplierAppId"] = arguments.get("supplierAppId")
                data = await client.get("/dsers-settings-bff/product/pro-shipping/get", **params)
                return reply(data)

            if name == "dsers_get_shipping_addresses":
                params = {k: v for k, v in arguments.items() if v is not None and k in ("page", "pageSize")}
                data = await client.get("/dsers-settings-bff/order/shipping-address", **params)
                return reply(data)

            if name == "dsers_add_shipping_address":
                address = arguments.get("address")
                if address is None:
                    return reply({"error": "address is required"})
                data = await client.post("/dsers-settings-bff/order/shipping-address", json=address)
                return reply(data)

            if name == "dsers_get_phone_list":
                data = await client.get("/dsers-settings-bff/order/phone-list")
                return reply(data)

            # --- Billing ---
            if name == "dsers_get_bill_list":
                params = {k: v for k, v in arguments.items() if v is not None and k in ("page", "pageSize")}
                data = await client.get("/dsers-pay-bff/v1/bill/list", **params)
                return reply(data)

            if name == "dsers_get_bill_detail":
                bill_id = arguments.get("billId")
                if not bill_id:
                    return reply({"error": "billId is required"})
                data = await client.get("/dsers-pay-bff/v1/bill/detail", billId=bill_id)
                return reply(data)

            if name == "dsers_get_payment_methods":
                data = await client.get("/dsers-pay-bff/v1/pay/methods")
                return reply(data)

            # --- Subscription Plan ---
            if name == "dsers_get_current_plan":
                data = await client.get("/dsers-plan-bff/plan")
                return reply(data)

            if name == "dsers_get_plan_limits":
                data = await client.get("/dsers-plan-bff/limit")
                return reply(data)

            if name == "dsers_get_all_plans":
                data = await client.get("/dsers-plan-bff/plan/all-type-limit")
                return reply(data)

            return reply({"error": f"Unknown tool: {name}"})

        except Exception as e:
            err_msg = str(e)
            err_detail = getattr(e, "body", None)
            status = getattr(e, "status", None)
            out: dict[str, Any] = {"error": err_msg}
            if status is not None:
                out["status"] = status
            if err_detail:
                out["detail"] = err_detail
            return reply(out)

    return TOOLS, handle
