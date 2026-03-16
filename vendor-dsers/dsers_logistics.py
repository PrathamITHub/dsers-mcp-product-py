"""DSers Logistics module — MCP tools for dsers-logistics-bff and dsers-tracking-bff APIs."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from mcp.types import TextContent, Tool

if TYPE_CHECKING:
    from dsers_mcp_base.client import DSersClient


def register(app: Any, client: "DSersClient") -> tuple[list[Tool], Any]:
    """Register all logistics-related MCP tools. Returns (TOOLS, handle)."""

    TOOLS = [
        # Tracking (dsers-logistics-bff)
        Tool(
            name="dsers_get_tracking_info",
            description="Get tracking information for a single tracking number.",
            inputSchema={
                "type": "object",
                "properties": {"trackingNumber": {"type": "string", "description": "Tracking number"}},
                "required": ["trackingNumber"],
            },
        ),
        Tool(
            name="dsers_batch_get_tracking",
            description="Get tracking information for multiple tracking numbers at once.",
            inputSchema={
                "type": "object",
                "properties": {"trackingNumbers": {"type": "array", "items": {"type": "string"}, "description": "List of tracking numbers"}},
                "required": ["trackingNumbers"],
            },
        ),
        Tool(
            name="dsers_get_tracking_detail",
            description="Get detailed tracking events and status for a tracking number.",
            inputSchema={
                "type": "object",
                "properties": {"trackingNumber": {"type": "string", "description": "Tracking number"}},
                "required": ["trackingNumber"],
            },
        ),
        Tool(
            name="dsers_get_user_logistics_settings",
            description="Get the user's logistics and tracking settings.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="dsers_update_logistics_settings",
            description="Update the user's logistics settings. Pass settings object in body.",
            inputSchema={
                "type": "object",
                "properties": {"settings": {"type": "object", "description": "Settings to update"}},
                "required": ["settings"],
            },
        ),
        Tool(
            name="dsers_export_logistics",
            description="Export logistics data. Pass filters in body.",
            inputSchema={
                "type": "object",
                "properties": {"filters": {"type": "object", "description": "Export filters (date range, status, etc.)"}},
                "required": ["filters"],
            },
        ),
        # Tracking Page (dsers-tracking-bff)
        Tool(
            name="dsers_create_tracking_page",
            description="Create a custom tracking page for customers.",
            inputSchema={
                "type": "object",
                "properties": {"config": {"type": "object", "description": "Page configuration (name, branding, etc.)"}},
                "required": ["config"],
            },
        ),
        Tool(
            name="dsers_get_tracking_page",
            description="Get a tracking page by pageId.",
            inputSchema={
                "type": "object",
                "properties": {"pageId": {"type": "string", "description": "Tracking page ID"}},
                "required": ["pageId"],
            },
        ),
        Tool(
            name="dsers_list_tracking_pages",
            description="List all tracking pages for the account.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="dsers_delete_tracking_page",
            description="Delete a tracking page.",
            inputSchema={
                "type": "object",
                "properties": {"pageId": {"type": "string", "description": "Tracking page ID to delete"}},
                "required": ["pageId"],
            },
        ),
        Tool(
            name="dsers_get_tracking_page_detail",
            description="Get tracking detail for a tracking number within a tracking page context.",
            inputSchema={
                "type": "object",
                "properties": {"trackingNumber": {"type": "string", "description": "Tracking number"}},
                "required": ["trackingNumber"],
            },
        ),
        Tool(
            name="dsers_get_tracking_page_status",
            description="Get status and stats for a tracking page.",
            inputSchema={
                "type": "object",
                "properties": {"pageId": {"type": "string", "description": "Tracking page ID"}},
                "required": ["pageId"],
            },
        ),
        # Shipping (dsers-logistics-bff)
        Tool(
            name="dsers_get_shipping_methods",
            description="Get available shipping methods/lines for a destination country.",
            inputSchema={
                "type": "object",
                "properties": {"country": {"type": "string", "description": "Destination country code"}},
                "required": ["country"],
            },
        ),
        Tool(
            name="dsers_get_import_order_status",
            description="Get status of an order import job.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]

    def reply(data: Any) -> list[TextContent]:
        return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]

    async def handle(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        try:
            # Tracking (dsers-logistics-bff)
            if name == "dsers_get_tracking_info":
                tracking = arguments.get("trackingNumber")
                if not tracking:
                    return reply({"error": "trackingNumber is required"})
                data = await client.get("/dsers-logistics-bff/v1/tracking/info", trackingNumber=tracking)
                return reply(data)

            if name == "dsers_batch_get_tracking":
                numbers = arguments.get("trackingNumbers", [])
                data = await client.post("/dsers-logistics-bff/v1/tracking/batch", json={"trackingNumbers": numbers})
                return reply(data)

            if name == "dsers_get_tracking_detail":
                tracking = arguments.get("trackingNumber")
                if not tracking:
                    return reply({"error": "trackingNumber is required"})
                data = await client.get("/dsers-logistics-bff/v1/tracking/detail", trackingNumber=tracking)
                return reply(data)

            if name == "dsers_get_user_logistics_settings":
                data = await client.get("/dsers-logistics-bff/v1/user/setting")
                return reply(data)

            if name == "dsers_update_logistics_settings":
                settings = arguments.get("settings", arguments)
                data = await client.post("/dsers-logistics-bff/v1/user/setting", json=settings)
                return reply(data)

            if name == "dsers_export_logistics":
                filters = arguments.get("filters", arguments)
                data = await client.post("/dsers-logistics-bff/v1/export", json=filters)
                return reply(data)

            # Tracking Page (dsers-tracking-bff)
            if name == "dsers_create_tracking_page":
                config = arguments.get("config", arguments)
                data = await client.post("/dsers-tracking-bff/tracking-page/create", json=config)
                return reply(data)

            if name == "dsers_get_tracking_page":
                page_id = arguments.get("pageId")
                if not page_id:
                    return reply({"error": "pageId is required"})
                data = await client.get("/dsers-tracking-bff/tracking-page/get", pageId=page_id)
                return reply(data)

            if name == "dsers_list_tracking_pages":
                data = await client.get("/dsers-tracking-bff/tracking-page/list")
                return reply(data)

            if name == "dsers_delete_tracking_page":
                page_id = arguments.get("pageId")
                if not page_id:
                    return reply({"error": "pageId is required"})
                data = await client.post("/dsers-tracking-bff/tracking-page/delete", json={"pageId": page_id})
                return reply(data)

            if name == "dsers_get_tracking_page_detail":
                tracking = arguments.get("trackingNumber")
                if not tracking:
                    return reply({"error": "trackingNumber is required"})
                data = await client.get("/dsers-tracking-bff/tracking-page/tracking-detail", trackingNumber=tracking)
                return reply(data)

            if name == "dsers_get_tracking_page_status":
                page_id = arguments.get("pageId")
                if not page_id:
                    return reply({"error": "pageId is required"})
                data = await client.get("/dsers-tracking-bff/tracking-page/status", pageId=page_id)
                return reply(data)

            # Shipping (dsers-logistics-bff)
            if name == "dsers_get_shipping_methods":
                country = arguments.get("country")
                if not country:
                    return reply({"error": "country is required"})
                data = await client.get("/dsers-logistics-bff/order/get-user-line-info", country=country)
                return reply(data)

            if name == "dsers_get_import_order_status":
                data = await client.get("/dsers-logistics-bff/order/import-status")
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
