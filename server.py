#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from dropship_import_mcp.job_store import FileJobStore
from dropship_import_mcp.provider import load_provider
from dropship_import_mcp.service import ImportFlowService

load_dotenv()

STATE_DIR = Path(os.getenv("IMPORT_MCP_STATE_DIR", Path(__file__).resolve().parent / ".state"))
PROVIDER = load_provider()
SERVICE = ImportFlowService(PROVIDER, FileJobStore(STATE_DIR))

app = Server("public-dropship-import-mcp")


def _reply_json(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


TOOLS = [
    Tool(
        name="get_rule_capabilities",
        description="Show supported rule families, stores, visibility modes, and push options for the currently loaded provider.",
        inputSchema={
            "type": "object",
            "properties": {
                "target_store": {"type": "string", "description": "Optional store ref or display name to inspect"},
            },
            "required": [],
        },
    ),
    Tool(
        name="validate_rules",
        description="Validate and normalize a structured rule object against the currently loaded provider before preparing an import candidate.",
        inputSchema={
            "type": "object",
            "properties": {
                "target_store": {"type": "string", "description": "Optional store ref or display name to validate against"},
                "rules": {
                    "type": "object",
                    "description": "Structured rule object with pricing, content, images, and optional instruction_text.",
                },
            },
            "required": ["rules"],
        },
    ),
    Tool(
        name="prepare_import_candidate",
        description="Resolve a source URL, prepare an import candidate, apply structured rules, and return a preview bundle.",
        inputSchema={
            "type": "object",
            "properties": {
                "source_url": {"type": "string", "description": "Source product URL"},
                "source_hint": {"type": "string", "description": "Optional source hint: auto, aliexpress, accio"},
                "country": {"type": "string", "description": "Target country code such as US"},
                "target_store": {"type": "string", "description": "Optional store ref or display name"},
                "visibility_mode": {"type": "string", "description": "backend_only or sell_immediately"},
                "rules": {
                    "type": "object",
                    "description": "Structured rule object with pricing, content, images, and optional instruction_text.",
                },
            },
            "required": ["source_url"],
        },
    ),
    Tool(
        name="get_import_preview",
        description="Load a previously prepared preview bundle by job_id.",
        inputSchema={
            "type": "object",
            "properties": {"job_id": {"type": "string", "description": "Prepared job id"}},
            "required": ["job_id"],
        },
    ),
    Tool(
        name="set_product_visibility",
        description="Update the requested visibility mode for a prepared job before confirmation.",
        inputSchema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Prepared job id"},
                "visibility_mode": {"type": "string", "description": "backend_only or sell_immediately"},
            },
            "required": ["job_id", "visibility_mode"],
        },
    ),
    Tool(
        name="confirm_push_to_store",
        description="Commit the prepared draft to the provider and request a store push after explicit confirmation.",
        inputSchema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Prepared job id"},
                "target_store": {"type": "string", "description": "Optional override for the target store"},
                "visibility_mode": {"type": "string", "description": "Optional override for backend_only or sell_immediately"},
                "push_options": {
                    "type": "object",
                    "description": "Optional provider-neutral publish settings such as publish_to_online_store, pricing_rule_behavior, image_strategy, and sales_channels.",
                },
            },
            "required": ["job_id"],
        },
    ),
    Tool(
        name="get_job_status",
        description="Get the current status for a prepared or pushed job.",
        inputSchema={
            "type": "object",
            "properties": {"job_id": {"type": "string", "description": "Prepared job id"}},
            "required": ["job_id"],
        },
    ),
]


_HANDLERS: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {
    "get_rule_capabilities": SERVICE.get_rule_capabilities,
    "validate_rules": SERVICE.validate_rules,
    "prepare_import_candidate": SERVICE.prepare_import_candidate,
    "get_import_preview": SERVICE.get_import_preview,
    "set_product_visibility": SERVICE.set_product_visibility,
    "confirm_push_to_store": SERVICE.confirm_push_to_store,
    "get_job_status": SERVICE.get_job_status,
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    handler = _HANDLERS.get(name)
    if handler is None:
        return _reply_json({"error": "Unknown tool", "available": sorted(_HANDLERS)})

    try:
        data = await handler(arguments or {})
        return _reply_json(data)
    except Exception as exc:
        return _reply_json({"error": str(exc)})


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
