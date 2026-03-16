"""DSers Order module — MCP tools for dsers-order-bff and dsers-order-search APIs."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from mcp.types import TextContent, Tool

if TYPE_CHECKING:
    from dsers_mcp_base.client import DSersClient


def register(app: Any, client: "DSersClient") -> tuple[list[Tool], Any]:
    """Register all order-related MCP tools. Returns (TOOLS, handle)."""

    TOOLS = [
        # Cart
        Tool(
            name="dsers_get_cart",
            description="Get current cart data including products, quantities, and totals.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="dsers_add_to_cart",
            description="Add products to the cart. Pass an array of product objects (productId, quantity, etc.).",
            inputSchema={
                "type": "object",
                "properties": {"products": {"type": "array", "items": {"type": "object"}, "description": "List of products to add"}},
                "required": ["products"],
            },
        ),
        Tool(
            name="dsers_update_cart_quantity",
            description="Update the quantity of a product in the cart.",
            inputSchema={
                "type": "object",
                "properties": {
                    "productId": {"type": "string", "description": "Product ID in cart"},
                    "quantity": {"type": "integer", "description": "New quantity"},
                },
                "required": ["productId", "quantity"],
            },
        ),
        Tool(
            name="dsers_remove_from_cart",
            description="Remove one or more products from the cart.",
            inputSchema={
                "type": "object",
                "properties": {"productIds": {"type": "array", "items": {"type": "string"}, "description": "Product IDs to remove"}},
                "required": ["productIds"],
            },
        ),
        Tool(
            name="dsers_save_cart_address",
            description="Save shipping/billing address for the cart.",
            inputSchema={
                "type": "object",
                "properties": {"address": {"type": "object", "description": "Address data object"}},
                "required": ["address"],
            },
        ),
        Tool(
            name="dsers_save_cart_shipping",
            description="Save the selected shipping method for the cart.",
            inputSchema={
                "type": "object",
                "properties": {"shippingMethod": {"type": "object", "description": "Shipping method object"}},
                "required": ["shippingMethod"],
            },
        ),
        Tool(
            name="dsers_save_cart_message",
            description="Save a message/note for the cart order.",
            inputSchema={
                "type": "object",
                "properties": {"message": {"type": "string", "description": "Order message or note"}},
                "required": ["message"],
            },
        ),
        # Order
        Tool(
            name="dsers_preview_order",
            description="Preview a wholesale order before placing it. Returns order summary and fees.",
            inputSchema={
                "type": "object",
                "properties": {"order": {"type": "object", "description": "Order preview data"}},
                "required": ["order"],
            },
        ),
        Tool(
            name="dsers_create_order",
            description="Create a wholesale order. Pass full order data in body.",
            inputSchema={
                "type": "object",
                "properties": {"order": {"type": "object", "description": "Order data for creation"}},
                "required": ["order"],
            },
        ),
        Tool(
            name="dsers_get_order_fee_info",
            description="Get fee information for a wholesale order. Pass orderId or items array.",
            inputSchema={
                "type": "object",
                "properties": {
                    "orderId": {"type": "string", "description": "Order ID (optional if items provided)"},
                    "items": {"type": "array", "items": {"type": "object"}, "description": "Order items (optional if orderId provided)"},
                },
                "required": [],
            },
        ),
        Tool(
            name="dsers_get_products_fee",
            description="Get fee information for a list of products.",
            inputSchema={
                "type": "object",
                "properties": {"products": {"type": "array", "items": {"type": "object"}, "description": "List of products"}},
                "required": ["products"],
            },
        ),
        # Order Search (dsers-order-search)
        Tool(
            name="dsers_search_orders",
            description="Search orders by keyword, status, store, date range. Supports pagination.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Search keyword"},
                    "status": {"type": "string", "description": "Order status filter"},
                    "storeId": {"type": "string", "description": "Store ID filter"},
                    "page": {"type": "integer", "description": "Page number"},
                    "pageSize": {"type": "integer", "description": "Items per page"},
                    "startDate": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                    "endDate": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                },
                "required": [],
            },
        ),
        Tool(
            name="dsers_get_order_detail",
            description="Get detailed information for a specific order by orderId.",
            inputSchema={
                "type": "object",
                "properties": {"orderId": {"type": "string", "description": "Order ID"}},
                "required": ["orderId"],
            },
        ),
        Tool(
            name="dsers_get_order_tracking",
            description="Get tracking information for an order.",
            inputSchema={
                "type": "object",
                "properties": {"orderId": {"type": "string", "description": "Order ID"}},
                "required": ["orderId"],
            },
        ),
        # Address & Rules
        Tool(
            name="dsers_get_address_rules",
            description="Get address validation rules configured for the account.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="dsers_get_addresses",
            description="Get list of saved addresses.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        # Invoice
        Tool(
            name="dsers_get_invoices",
            description="Get invoice list with pagination.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "Page number"},
                    "pageSize": {"type": "integer", "description": "Items per page"},
                },
                "required": [],
            },
        ),
        Tool(
            name="dsers_download_invoice",
            description="Download invoices. Pass invoice filters as params.",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoiceIds": {"type": "array", "items": {"type": "string"}, "description": "Invoice IDs to download"},
                    "startDate": {"type": "string", "description": "Start date filter"},
                    "endDate": {"type": "string", "description": "End date filter"},
                },
                "required": [],
            },
        ),
        # Report
        Tool(
            name="dsers_get_order_report",
            description="Get order summary report for a date range and optional store.",
            inputSchema={
                "type": "object",
                "properties": {
                    "startDate": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                    "endDate": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                    "storeId": {"type": "string", "description": "Store ID filter (optional)"},
                },
                "required": ["startDate", "endDate"],
            },
        ),
    ]

    def reply(data: Any) -> list[TextContent]:
        return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]

    async def handle(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        try:
            # Cart
            if name == "dsers_get_cart":
                data = await client.get("/dsers-order-bff/v1/get-cart-data")
                return reply(data)

            if name == "dsers_add_to_cart":
                products = arguments.get("products", [])
                data = await client.post("/dsers-order-bff/v1/add-products-cart-data", json={"products": products})
                return reply(data)

            if name == "dsers_update_cart_quantity":
                body = {
                    "productId": arguments.get("productId"),
                    "quantity": arguments.get("quantity"),
                }
                data = await client.post("/dsers-order-bff/v1/save-cart-product-quantity", json=body)
                return reply(data)

            if name == "dsers_remove_from_cart":
                product_ids = arguments.get("productIds", [])
                data = await client.post("/dsers-order-bff/v1/delete-products-cart-data", json={"productIds": product_ids})
                return reply(data)

            if name == "dsers_save_cart_address":
                address = arguments.get("address", arguments)
                data = await client.post("/dsers-order-bff/v1/save-cart-address", json=address)
                return reply(data)

            if name == "dsers_save_cart_shipping":
                shipping = arguments.get("shippingMethod", arguments)
                data = await client.post("/dsers-order-bff/v1/save-cart-shipping-method", json=shipping)
                return reply(data)

            if name == "dsers_save_cart_message":
                msg = arguments.get("message", "")
                data = await client.post("/dsers-order-bff/v1/save-cart-message", json={"message": msg})
                return reply(data)

            # Order
            if name == "dsers_preview_order":
                order = arguments.get("order", arguments)
                data = await client.post("/dsers-order-bff/v1/preview-wholesale-order", json=order)
                return reply(data)

            if name == "dsers_create_order":
                order = arguments.get("order", arguments)
                data = await client.post("/dsers-order-bff/v1/create-wholesale-order-v2", json=order)
                return reply(data)

            if name == "dsers_get_order_fee_info":
                body = {k: v for k, v in arguments.items() if v is not None and k in ("orderId", "items")}
                data = await client.post("/dsers-order-bff/v1/get-wholesale-order-fee-info-v2", json=body)
                return reply(data)

            if name == "dsers_get_products_fee":
                products = arguments.get("products", [])
                data = await client.post("/dsers-order-bff/v1/get-products-fee", json={"products": products})
                return reply(data)

            # Order Search
            if name == "dsers_search_orders":
                params = {k: v for k, v in arguments.items() if v is not None and k in ("keyword", "status", "storeId", "page", "pageSize", "startDate", "endDate")}
                data = await client.get("/dsers-order-search/v1/search", **params)
                return reply(data)

            if name == "dsers_get_order_detail":
                order_id = arguments.get("orderId")
                if not order_id:
                    return reply({"error": "orderId is required"})
                data = await client.get("/dsers-order-search/v1/order", orderId=order_id)
                return reply(data)

            if name == "dsers_get_order_tracking":
                order_id = arguments.get("orderId")
                if not order_id:
                    return reply({"error": "orderId is required"})
                data = await client.get("/dsers-order-search/v1/tracking", orderId=order_id)
                return reply(data)

            # Address & Rules
            if name == "dsers_get_address_rules":
                data = await client.get("/dsers-order-bff/v1/address/rules")
                return reply(data)

            if name == "dsers_get_addresses":
                data = await client.get("/dsers-order-bff/v1/address/list")
                return reply(data)

            # Invoice
            if name == "dsers_get_invoices":
                params = {k: v for k, v in arguments.items() if v is not None and k in ("page", "pageSize")}
                data = await client.get("/dsers-order-bff/v1/invoices", **params)
                return reply(data)

            if name == "dsers_download_invoice":
                params = {k: v for k, v in arguments.items() if v is not None}
                data = await client.get("/dsers-order-bff/v1/down-invoices", **params)
                return reply(data)

            # Report
            if name == "dsers_get_order_report":
                params = {k: v for k, v in arguments.items() if v is not None and k in ("startDate", "endDate", "storeId")}
                data = await client.get("/dsers-order-bff/v1/report/summary", **params)
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
