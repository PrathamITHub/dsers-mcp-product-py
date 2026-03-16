"""DSers Account module — MCP tools for account-user-bff API."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from mcp.types import TextContent, Tool

if TYPE_CHECKING:
    from dsers_mcp_base.client import DSersClient


def register(app: Any, client: "DSersClient") -> tuple[list[Tool], Any]:
    """Register all account-related MCP tools. Returns (TOOLS, handle)."""

    TOOLS = [
        Tool(
            name="dsers_login",
            description="Log in to DSers with stored credentials. Returns session_id and state. Use when you need to establish or refresh a DSers session.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="dsers_get_user_info",
            description="Get the current logged-in user's profile information (nickname, avatar, email, etc.).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="dsers_update_user_info",
            description="Update the current user's profile. Pass nickname, avatar, or other editable fields in the body.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nickname": {"type": "string", "description": "User display name"},
                    "avatar": {"type": "string", "description": "Avatar URL"},
                    "phone": {"type": "string", "description": "Phone number"},
                },
                "required": [],
            },
        ),
        Tool(
            name="dsers_list_stores",
            description="List all stores linked to the DSers account. Returns store IDs, names, platforms, and status.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="dsers_get_store_detail",
            description="Get detailed information for a specific store by storeId.",
            inputSchema={
                "type": "object",
                "properties": {
                    "storeId": {"type": "string", "description": "The store ID to fetch"},
                },
                "required": ["storeId"],
            },
        ),
        Tool(
            name="dsers_bind_store",
            description="Bind a new store to the DSers account. Requires platform and authCode (OAuth authorization code from the marketplace).",
            inputSchema={
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "description": "Store platform (e.g. aliexpress, shopify)"},
                    "authCode": {"type": "string", "description": "OAuth authorization code from marketplace"},
                },
                "required": ["platform", "authCode"],
            },
        ),
        Tool(
            name="dsers_unbind_store",
            description="Unbind (disconnect) a store from the DSers account.",
            inputSchema={
                "type": "object",
                "properties": {
                    "storeId": {"type": "string", "description": "The store ID to unbind"},
                },
                "required": ["storeId"],
            },
        ),
        Tool(
            name="dsers_list_staff",
            description="List all staff members with access to the DSers account.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="dsers_invite_staff",
            description="Invite a new staff member by email with specified permissions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email address to invite"},
                    "permissions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of permission codes (e.g. order_view, product_edit)",
                    },
                },
                "required": ["email", "permissions"],
            },
        ),
        Tool(
            name="dsers_remove_staff",
            description="Remove a staff member from the account.",
            inputSchema={
                "type": "object",
                "properties": {
                    "staffId": {"type": "string", "description": "The staff ID to remove"},
                },
                "required": ["staffId"],
            },
        ),
        Tool(
            name="dsers_update_staff_permission",
            description="Update a staff member's permissions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "staffId": {"type": "string", "description": "The staff ID to update"},
                    "permissions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New list of permission codes",
                    },
                },
                "required": ["staffId", "permissions"],
            },
        ),
        Tool(
            name="dsers_list_suppliers",
            description="List all suppliers configured for the DSers account.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="dsers_get_supplier_config",
            description="Get or set supplier configuration. Use POST to update config; pass config fields in the body.",
            inputSchema={
                "type": "object",
                "properties": {
                    "supplierId": {"type": "string", "description": "Supplier ID (optional for setting)"},
                    "config": {
                        "type": "object",
                        "description": "Config key-value pairs to set (optional)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="dsers_list_apps",
            description="List installed or available DSers apps/integrations.",
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
            if name == "dsers_login":
                data = await client.login()
                return reply(data)

            if name == "dsers_get_user_info":
                data = await client.get("/account-user-bff/v1/users/info")
                return reply(data)

            if name == "dsers_update_user_info":
                body = {k: v for k, v in arguments.items() if v is not None}
                data = await client.post("/account-user-bff/v1/users/info", json=body)
                return reply(data)

            if name == "dsers_list_stores":
                data = await client.post("/account-user-bff/v1/stores/user/list")
                return reply(data)

            if name == "dsers_get_store_detail":
                store_id = arguments.get("storeId")
                if not store_id:
                    return reply({"error": "storeId is required"})
                data = await client.get("/account-user-bff/v1/stores/detail", storeId=store_id)
                return reply(data)

            if name == "dsers_bind_store":
                body = {
                    "platform": arguments.get("platform"),
                    "authCode": arguments.get("authCode"),
                }
                if not body["platform"] or not body["authCode"]:
                    return reply({"error": "platform and authCode are required"})
                data = await client.post("/account-user-bff/v1/stores/bindStore", json=body)
                return reply(data)

            if name == "dsers_unbind_store":
                store_id = arguments.get("storeId")
                if not store_id:
                    return reply({"error": "storeId is required"})
                data = await client.post("/account-user-bff/v1/stores/unbind", json={"storeId": store_id})
                return reply(data)

            if name == "dsers_list_staff":
                data = await client.post("/account-user-bff/v1/staffs/list")
                return reply(data)

            if name == "dsers_invite_staff":
                body = {
                    "email": arguments.get("email"),
                    "permissions": arguments.get("permissions", []),
                }
                if not body["email"]:
                    return reply({"error": "email is required"})
                data = await client.post("/account-user-bff/v1/staffs/invite", json=body)
                return reply(data)

            if name == "dsers_remove_staff":
                staff_id = arguments.get("staffId")
                if not staff_id:
                    return reply({"error": "staffId is required"})
                data = await client.post("/account-user-bff/v1/staffs/remove", json={"staffId": staff_id})
                return reply(data)

            if name == "dsers_update_staff_permission":
                body = {
                    "staffId": arguments.get("staffId"),
                    "permissions": arguments.get("permissions", []),
                }
                if not body["staffId"]:
                    return reply({"error": "staffId is required"})
                data = await client.post("/account-user-bff/v1/staffs/permission", json=body)
                return reply(data)

            if name == "dsers_list_suppliers":
                data = await client.get("/account-user-bff/v1/suppliers/list")
                return reply(data)

            if name == "dsers_get_supplier_config":
                body = {k: v for k, v in arguments.items() if v is not None}
                data = await client.post("/account-user-bff/v1/suppliers/config/set", json=body)
                return reply(data)

            if name == "dsers_list_apps":
                data = await client.get("/account-user-bff/v1/apps/list")
                return reply(data)

            return reply({"error": f"Unknown tool: {name}"})

        except Exception as e:
            err_msg = str(e)
            err_detail = getattr(e, "body", None)
            status = getattr(e, "status", None)
            out = {"error": err_msg}
            if status is not None:
                out["status"] = status
            if err_detail:
                out["detail"] = err_detail
            return reply(out)

    return TOOLS, handle
