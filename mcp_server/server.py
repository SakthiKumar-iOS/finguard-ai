# mcp_server/server.py
# Purpose: Define and start the FastMCP server for tool access.

import logging
import re

from fastmcp import FastMCP

from config.settings import MCP_HOST, MCP_PORT
from mcp_server.tools import (
    get_transactions,
    get_flagged_transactions,
    get_products,
    get_balance,
    check_eligibility,
    create_service_request,
    write_audit_entry,
    get_audit_log,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------
_USER_ID_RE = re.compile(r"^U\d{3}$")
_VALID_REQUEST_TYPES = {"dispute", "freeze", "lost_stolen", "callback", "complaint", "cancel"}
_INVALID = {"error": "Invalid input"}


def _ok_user_id(user_id: str) -> bool:
    return bool(_USER_ID_RE.match(str(user_id or "")))


def _ok_product_type(pt: str) -> bool:
    return isinstance(pt, str) and 0 < len(pt.strip()) <= 50


def _ok_limit(limit: int) -> bool:
    return isinstance(limit, int) and 1 <= limit <= 100


def _ok_description(desc: str) -> bool:
    return isinstance(desc, str) and len(desc.strip()) <= 500


# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "finguard-tools",
    instructions=(
        "FinGuard AI local tool hub — all tools run locally on macOS, no external calls"
    ),
)


@mcp.tool()
def tool_get_transactions(user_id: str = "U001") -> dict:
    """Retrieve transactions for a user. user_id must match U[0-9]{3}."""
    if not _ok_user_id(user_id):
        return _INVALID
    return get_transactions(user_id)


@mcp.tool()
def tool_get_flagged_transactions(user_id: str = "U001") -> dict:
    """Retrieve only flagged (unusual) transactions for a user."""
    if not _ok_user_id(user_id):
        return _INVALID
    return get_flagged_transactions(user_id)


@mcp.tool()
def tool_get_products(product_type: str = "all") -> dict:
    """Retrieve banking products, optionally filtered by product type."""
    if not _ok_product_type(product_type):
        return _INVALID
    return get_products(product_type)


@mcp.tool()
def tool_get_balance(user_id: str = "U001") -> dict:
    """Retrieve the current account balance for a user."""
    if not _ok_user_id(user_id):
        return _INVALID
    return get_balance(user_id)


@mcp.tool()
def tool_check_eligibility(product_type: str, user_id: str = "U001") -> dict:
    """Check whether the demo user is eligible for a given product type."""
    if not _ok_product_type(product_type):
        return _INVALID
    if not _ok_user_id(user_id):
        return _INVALID
    return check_eligibility(product_type, user_id)


@mcp.tool()
def tool_create_service_request(request_type: str, description: str) -> dict:
    """Create a service request. request_type must be one of the allowed types."""
    if not isinstance(request_type, str) or request_type.strip().lower() not in _VALID_REQUEST_TYPES:
        return {"error": "Invalid request type"}
    if not _ok_description(description):
        return _INVALID
    return create_service_request(request_type, description[:500].strip())


@mcp.tool()
def tool_write_audit_entry(intent: str, status: str, metadata: dict = None) -> bool:
    """Write a sanitised audit log entry. Never include PII or original user input."""
    if not isinstance(intent, str) or not isinstance(status, str):
        return False
    return write_audit_entry(intent[:50], status[:20], metadata or {})


@mcp.tool()
def tool_get_audit_log(limit: int = 10) -> dict:
    """Retrieve the last N audit log entries (max 100). Returns timestamp, intent, status only."""
    if not _ok_limit(limit):
        return _INVALID
    return get_audit_log(limit)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def start_server() -> None:
    """Start the FinGuard MCP server."""
    logger.info("FinGuard MCP Server started on %s:%s", MCP_HOST, MCP_PORT)
    try:
        mcp.run(transport="streamable-http", host=MCP_HOST, port=MCP_PORT)
    finally:
        logger.info("FinGuard MCP Server stopped")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_server()
