# agents/product_query.py
# Purpose: Answers queries about financial products by querying a knowledge base.

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_FILE = Path(__file__).parent.parent / "data" / "knowledge_base" / "products.json"
_DISCLAIMER = (
    "Rates and fees are indicative only. Please visit a branch or call us for personalised advice."
)


class ProductQueryAgent:
    """Agent that queries the products database to provide information about financial products."""

    def __init__(self) -> None:
        self._products: list[dict] = []
        try:
            with open(_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._products = data.get("products", [])
        except FileNotFoundError:
            logger.warning("ProductQueryAgent: data file not found at %s", _DATA_FILE)
        except Exception as exc:  # noqa: BLE001
            logger.error("ProductQueryAgent: failed to load data: %s", type(exc).__name__)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, input: str) -> str:  # noqa: A002
        """Answer a product query based on keywords in *input*."""
        try:
            if not self._products:
                return "Product information unavailable."

            lowered = (input or "").lower()

            # --- Detect two products for comparison ---
            matched = [p for p in self._products if self._name_matches(p, lowered)]
            if len(matched) >= 2:
                return self._compare(matched[0], matched[1])

            # --- Specific product lookup ---
            if matched:
                return self._describe(matched[0])

            # --- Type-based listing ---
            type_map = {
                "savings": "savings",
                "term deposit": "term_deposit",
                "personal loan": "personal_loan",
                "home loan": "home_loan",
                "mortgage": "home_loan",
                "credit card": "credit_card",
                "card": "credit_card",
                "loan": "personal_loan",
                "insurance": None,
                "investment": None,
            }
            for keyword, ptype in type_map.items():
                if keyword in lowered and ptype:
                    return self._list_by_type(ptype)

            # --- Fallback: list all ---
            return self._list_all()

        except Exception as exc:  # noqa: BLE001
            logger.error("ProductQueryAgent: unexpected error type=%s", type(exc).__name__)
            return "Unable to retrieve product information. Please try again."

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _name_matches(self, product: dict, text: str) -> bool:
        name_tokens = product["name"].lower().split()
        return any(token in text for token in name_tokens if len(token) > 3)

    def _describe(self, p: dict) -> str:
        fees_str = "  ".join(f"{k.replace('_', ' ').capitalize()}: {v}" for k, v in p["fees"].items())
        features_str = "\n  - ".join(p["features"])
        eligibility_str = "\n  - ".join(p["eligibility_criteria"])
        max_amt = "No limit" if p["max_amount"] is None else f"AUD {p['max_amount']:,}"
        response = (
            f"{p['name']} ({p['type'].replace('_', ' ').title()})\n\n"
            f"Description: {p['description']}\n\n"
            f"Interest Rate: {p['interest_rate']}\n"
            f"Amount Range: AUD {p['min_amount']:,} – {max_amt}\n"
            f"Term: {p['term']}\n\n"
            f"Fees:\n  {fees_str}\n\n"
            f"Key Features:\n  - {features_str}\n\n"
            f"Eligibility:\n  - {eligibility_str}\n\n"
            f"{_DISCLAIMER}"
        )
        return response

    def _compare(self, p1: dict, p2: dict) -> str:
        def _rate(p):
            return p.get("interest_rate", "N/A")

        def _fee(p):
            return next(iter(p["fees"].values()), "N/A")

        response = (
            f"Comparison: {p1['name']} vs {p2['name']}\n\n"
            f"{'Feature':<25} {'Product 1':<30} {'Product 2':<30}\n"
            f"{'-'*85}\n"
            f"{'Name':<25} {p1['name']:<30} {p2['name']:<30}\n"
            f"{'Type':<25} {p1['type'].replace('_',' ').title():<30} {p2['type'].replace('_',' ').title():<30}\n"
            f"{'Interest Rate':<25} {_rate(p1):<30} {_rate(p2):<30}\n"
            f"{'Term':<25} {p1['term']:<30} {p2['term']:<30}\n\n"
            f"{_DISCLAIMER}"
        )
        return response

    def _list_by_type(self, ptype: str) -> str:
        matches = [p for p in self._products if p["type"] == ptype]
        if not matches:
            return f"No products found for type '{ptype}'.\n\n{_DISCLAIMER}"
        lines = [f"Available {ptype.replace('_', ' ').title()} products:\n"]
        for p in matches:
            lines.append(f"  • {p['name']} — {p['interest_rate']}")
        lines.append(f"\n{_DISCLAIMER}")
        return "\n".join(lines)

    def _list_all(self) -> str:
        lines = ["Our available banking products:\n"]
        current_type = ""
        for p in self._products:
            ptype = p["type"].replace("_", " ").title()
            if ptype != current_type:
                lines.append(f"\n{ptype}:")
                current_type = ptype
            lines.append(f"  • {p['name']} — {p['interest_rate']}")
        lines.append(f"\n{_DISCLAIMER}")
        return "\n".join(lines)
