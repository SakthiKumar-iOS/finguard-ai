# mcp_server/tools.py
# Purpose: Define tools exposed by the MCP server.

import json
import logging
import os
import random
import re
from datetime import datetime, timezone
from pathlib import Path

from config.settings import TRANSACTIONS_FILE, PRODUCTS_FILE, AUDIT_LOG_DIR

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_USER_ID_RE = re.compile(r"^U\d{3}$")
_VALID_REQUEST_TYPES = {"dispute", "freeze", "lost_stolen", "callback", "complaint", "cancel"}

# Hardcoded eligibility rules (mirror agents/eligibility.py)
_DEMO_USER_PROFILE = {
    "age": 32,
    "annual_income": 75000,
    "employment": "full-time",
    "credit_score": 720,
    "has_defaults": False,
    "has_bankruptcy": False,
    "deposit_available": 80000,
}

_ELIGIBILITY_RULES: dict[str, dict] = {
    "personal_loan": {"min_income": 30000, "min_age": 18, "no_defaults": True},
    "home_loan": {"min_income": 60000, "min_age": 18, "min_deposit_pct": 10},
    "credit_card": {"min_income": 25000, "min_age": 18, "no_bankruptcies": True},
    "term_deposit": {"min_amount": 1000},
    "savings_account": {"min_age": 18},
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_user_id(user_id: str) -> bool:
    """Return True if user_id matches U[0-9]{3}."""
    return bool(_USER_ID_RE.match(str(user_id or "")))


def _mask_account(account: str) -> str:
    """Ensure account number is masked (show last 4 only)."""
    if not account:
        return "****XXXX"
    # If already masked keep it; otherwise mask
    if "****" in account:
        return account
    return "****" + str(account)[-4:]


def _load_json(filepath: str) -> dict | list | None:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("tools: file not found: %s", Path(filepath).name)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("tools: error loading file type=%s", type(exc).__name__)
        return None


def _ref() -> str:
    """Generate a synthetic service request reference."""
    return "SR" + "".join(str(random.randint(0, 9)) for _ in range(8))


def _audit_log_path() -> Path:
    """Return the path to today's audit log file."""
    audit_dir = Path(AUDIT_LOG_DIR)
    audit_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return audit_dir / f"audit_{date_str}.jsonl"


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

def get_transactions(user_id: str = "U001") -> dict:
    """Return transactions for *user_id* with masked account numbers."""
    try:
        if not _validate_user_id(user_id):
            return {"error": "Invalid input"}

        data = _load_json(TRANSACTIONS_FILE)
        if data is None:
            return {"error": "Data unavailable"}

        users = data.get("users", {})
        user = users.get(user_id)
        if not user:
            return {"error": "User not found"}

        profile = dict(user.get("profile", {}))
        profile["account_number"] = _mask_account(profile.get("account_number", ""))

        transactions = user.get("transactions", [])

        return {
            "user_id": user_id,
            "profile": profile,
            "transactions": transactions,
            "count": len(transactions),
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("get_transactions: error type=%s", type(exc).__name__)
        return {"error": "Data unavailable"}


def get_flagged_transactions(user_id: str = "U001") -> dict:
    """Return only flagged transactions for *user_id*."""
    try:
        if not _validate_user_id(user_id):
            return {"error": "Invalid input"}

        data = _load_json(TRANSACTIONS_FILE)
        if data is None:
            return {"error": "Data unavailable"}

        users = data.get("users", {})
        user = users.get(user_id)
        if not user:
            return {"transactions": [], "count": 0}

        flagged = [t for t in user.get("transactions", []) if t.get("flagged")]
        return {"transactions": flagged, "count": len(flagged)}
    except Exception as exc:  # noqa: BLE001
        logger.error("get_flagged_transactions: error type=%s", type(exc).__name__)
        return {"transactions": [], "count": 0}


def get_products(product_type: str = "all") -> dict:
    """Return banking products, optionally filtered by *product_type*."""
    try:
        if not isinstance(product_type, str) or len(product_type) > 50:
            return {"error": "Invalid input"}

        data = _load_json(PRODUCTS_FILE)
        if data is None:
            return {"error": "Data unavailable"}

        products: list[dict] = data.get("products", [])

        if product_type.strip().lower() != "all":
            filter_type = product_type.strip().lower()
            products = [p for p in products if p.get("type", "").lower() == filter_type]

        if not products:
            return {"products": [], "count": 0}

        return {"products": products, "count": len(products)}
    except Exception as exc:  # noqa: BLE001
        logger.error("get_products: error type=%s", type(exc).__name__)
        return {"products": [], "count": 0}


def get_balance(user_id: str = "U001") -> dict:
    """Return the balance from the most recent transaction for *user_id*."""
    try:
        if not _validate_user_id(user_id):
            return {"error": "Invalid input"}

        data = _load_json(TRANSACTIONS_FILE)
        if data is None:
            return {"error": "Balance unavailable"}

        users = data.get("users", {})
        user = users.get(user_id)
        if not user:
            return {"error": "Balance unavailable"}

        transactions = user.get("transactions", [])
        if not transactions:
            return {"error": "Balance unavailable"}

        latest = transactions[0]  # Assumed sorted newest-first in data file
        return {
            "balance": latest.get("balance_after", 0.0),
            "currency": "AUD",
            "as_of": latest.get("date", ""),
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("get_balance: error type=%s", type(exc).__name__)
        return {"error": "Balance unavailable"}


def check_eligibility(product_type: str, user_id: str = "U001") -> dict:
    """Check demo user eligibility for *product_type*."""
    try:
        if not isinstance(product_type, str) or len(product_type) > 50:
            return {"error": "Invalid input"}
        if not _validate_user_id(user_id):
            return {"error": "Invalid input"}

        ptype = product_type.strip().lower()
        rules = _ELIGIBILITY_RULES.get(ptype)
        if not rules:
            return {
                "eligible": False,
                "reason": "Product type not recognised. Valid types: personal_loan, home_loan, credit_card, term_deposit, savings_account.",
                "product_type": ptype,
            }

        user = _DEMO_USER_PROFILE
        failures: list[str] = []

        if "min_age" in rules and user["age"] < rules["min_age"]:
            failures.append(f"Age below minimum requirement of {rules['min_age']}")

        if "min_income" in rules and user["annual_income"] < rules["min_income"]:
            failures.append("Income does not meet minimum requirement")

        if rules.get("no_defaults") and user["has_defaults"]:
            failures.append("Credit defaults on record")

        if rules.get("no_bankruptcies") and user["has_bankruptcy"]:
            failures.append("Bankruptcy history on record")

        if "min_deposit_pct" in rules:
            representative_value = 500000
            required = representative_value * rules["min_deposit_pct"] / 100
            if user["deposit_available"] < required:
                failures.append(f"Deposit does not meet minimum {rules['min_deposit_pct']}% requirement")

        eligible = len(failures) == 0
        reason = "All eligibility criteria met." if eligible else "; ".join(failures)

        return {"eligible": eligible, "reason": reason, "product_type": ptype}
    except Exception as exc:  # noqa: BLE001
        logger.error("check_eligibility: error type=%s", type(exc).__name__)
        return {"error": "Eligibility check unavailable"}


def create_service_request(request_type: str, description: str) -> dict:
    """Log a service request and return a synthetic reference number.

    The *description* is never stored or logged.
    """
    try:
        if not isinstance(request_type, str):
            return {"error": "Invalid input"}

        rtype = request_type.strip().lower()
        if rtype not in _VALID_REQUEST_TYPES:
            return {"error": "Invalid request type"}

        # description validated for length only — never stored
        if not isinstance(description, str) or len(description) > 500:
            return {"error": "Invalid input"}

        reference = _ref()
        logger.info("create_service_request: type=%s reference=%s", rtype, reference)

        return {
            "reference": reference,
            "status": "received",
            "request_type": rtype,
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("create_service_request: error type=%s", type(exc).__name__)
        return {"error": "Service request unavailable"}


def write_audit_entry(intent: str, status: str, metadata: dict = None) -> bool:
    """Write a sanitised audit entry to the daily .jsonl log file.

    Never writes original user input or PII.
    """
    try:
        if metadata is None:
            metadata = {}

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "intent": str(intent)[:50],
            "status": str(status)[:20],
            "metadata": {k: v for k, v in metadata.items() if k not in ("input", "text", "pii")},
        }

        log_path = _audit_log_path()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("write_audit_entry: error type=%s", type(exc).__name__)
        return False


def get_audit_log(limit: int = 10) -> dict:
    """Return the last *limit* sanitised audit log entries."""
    try:
        if not isinstance(limit, int) or not (1 <= limit <= 100):
            return {"error": "Invalid input"}

        audit_dir = Path(AUDIT_LOG_DIR)
        if not audit_dir.exists():
            return {"entries": [], "count": 0}

        jsonl_files = sorted(
            audit_dir.glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not jsonl_files:
            return {"entries": [], "count": 0}

        entries: list[dict] = []
        with open(jsonl_files[0], "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                    # Return only safe fields — never original input
                    entries.append({
                        "timestamp": raw.get("timestamp", ""),
                        "intent": raw.get("intent", ""),
                        "status": raw.get("status", ""),
                    })
                except json.JSONDecodeError:
                    continue

        recent = entries[-limit:][::-1]
        return {"entries": recent, "count": len(recent)}
    except Exception as exc:  # noqa: BLE001
        logger.error("get_audit_log: error type=%s", type(exc).__name__)
        return {"entries": [], "count": 0}
