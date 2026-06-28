# agents/transaction_analyst.py
# Purpose: Analyzes bank transactions to flag anomalies or explain user spending patterns.

import json
import logging
import os
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_FILE = Path(__file__).parent.parent / "data" / "transactions" / "mock_transactions.json"
_DEFAULT_USER = "U001"


class TransactionAnalystAgent:
    """Agent that performs detailed analysis and verification of transaction records."""

    def __init__(self) -> None:
        self._data: dict = {}
        try:
            with open(_DATA_FILE, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except FileNotFoundError:
            logger.warning("TransactionAnalystAgent: data file not found at %s", _DATA_FILE)
        except Exception as exc:  # noqa: BLE001
            logger.error("TransactionAnalystAgent: failed to load data: %s", type(exc).__name__)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, input: str) -> str:  # noqa: A002
        """Analyse transactions for the demo user based on the query in *input*."""
        try:
            if not self._data:
                return "Transaction data unavailable."

            user = self._data.get("users", {}).get(_DEFAULT_USER)
            if not user:
                return "Transaction data unavailable."

            transactions: list[dict] = user.get("transactions", [])
            profile: dict = user.get("profile", {})
            account_num: str = profile.get("account_number", "****XXXX")

            lowered = (input or "").lower()

            # --- Route to capability ---
            if any(kw in lowered for kw in ["unusual", "suspicious", "flagged", "flag", "anomaly"]):
                return self._unusual_spending(transactions, account_num)

            if any(kw in lowered for kw in ["category", "breakdown", "summary", "categoris", "spending pattern"]):
                return self._spending_summary(transactions)

            if any(kw in lowered for kw in ["balance"]):
                return self._balance(transactions, account_num)

            # Default: recent transactions
            return self._recent_transactions(transactions, account_num)

        except Exception as exc:  # noqa: BLE001
            logger.error("TransactionAnalystAgent: unexpected error type=%s", type(exc).__name__)
            return "Unable to retrieve transactions. Please try again."

    # ------------------------------------------------------------------
    # Capabilities
    # ------------------------------------------------------------------

    def _recent_transactions(self, transactions: list[dict], account_num: str) -> str:
        recent = transactions[:10]
        lines = [f"Recent transactions for account {account_num}:\n"]
        for t in recent:
            direction = "+" if t["type"] == "credit" else "-"
            lines.append(
                f"  {t['date']}  {direction}AUD {t['amount']:>9.2f}  "
                f"{t['category'].capitalize():<15} {t['merchant']}"
            )
        lines.append(f"\n{len(recent)} transaction(s) shown.")
        return "\n".join(lines)

    def _unusual_spending(self, transactions: list[dict], account_num: str) -> str:
        flagged = [t for t in transactions if t.get("flagged")]
        if not flagged:
            return (
                f"No unusual transactions detected on account {account_num}. "
                "Your spending patterns appear normal."
            )
        lines = [
            f"Unusual transactions detected on account {account_num}. "
            f"Please review the following:\n"
        ]
        for t in flagged:
            lines.append(
                f"  {t['date']}  AUD {t['amount']:>9.2f}  {t['merchant']}\n"
                f"          {t['description']}"
            )
        lines.append(
            "\nIf you do not recognise any of these transactions, please contact us immediately."
        )
        return "\n".join(lines)

    def _spending_summary(self, transactions: list[dict]) -> str:
        totals: dict[str, float] = defaultdict(float)
        for t in transactions:
            if t["type"] == "debit":
                totals[t["category"]] += t["amount"]
        if not totals:
            return "No spending data available."
        lines = ["Spending summary by category (debits only):\n"]
        for cat, total in sorted(totals.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {cat.capitalize():<20} AUD {total:>9.2f}")
        return "\n".join(lines)

    def _balance(self, transactions: list[dict], account_num: str) -> str:
        if not transactions:
            return "Balance information is currently unavailable."
        latest = transactions[0]
        balance = latest.get("balance_after", 0.0)
        return (
            f"Current balance for account {account_num}: AUD {balance:,.2f}\n"
            f"As of: {latest['date']}"
        )
