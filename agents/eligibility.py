# agents/eligibility.py
# Purpose: Determines user eligibility for specific financial products or loans.

import logging

logger = logging.getLogger(__name__)

_DISCLAIMER = (
    "This is a general eligibility guide only. Final approval is subject to "
    "full assessment and credit check."
)

# ---------------------------------------------------------------------------
# Demo user profile (synthetic — no real data)
# ---------------------------------------------------------------------------
_DEMO_USER = {
    "age": 32,
    "annual_income": 75000,
    "employment": "full-time",
    "credit_score": 720,
    "has_defaults": False,
    "has_bankruptcy": False,
    "deposit_available": 80000,
}

# ---------------------------------------------------------------------------
# Hardcoded eligibility rules
# ---------------------------------------------------------------------------
_RULES: dict[str, dict] = {
    "personal_loan": {
        "min_income": 30000,
        "min_age": 18,
        "no_defaults": True,
    },
    "home_loan": {
        "min_income": 60000,
        "min_age": 18,
        "min_deposit_pct": 10,
    },
    "credit_card": {
        "min_income": 25000,
        "min_age": 18,
        "no_bankruptcies": True,
    },
    "term_deposit": {
        "min_amount": 1000,
    },
    "savings_account": {
        "min_age": 18,
    },
}

# Keyword → rule key mapping
_KEYWORD_MAP: list[tuple[list[str], str]] = [
    (["personal loan", "personal"], "personal_loan"),
    (["home loan", "home", "mortgage", "house"], "home_loan"),
    (["credit card", "platinum card", "basic card", "card"], "credit_card"),
    (["term deposit", "term"], "term_deposit"),
    (["savings account", "savings"], "savings_account"),
]


class EligibilityAgent:
    """Agent that evaluates financial parameters to check product eligibility rules."""

    def run(self, input: str) -> str:  # noqa: A002
        """Check eligibility for a product type detected from *input*."""
        try:
            lowered = (input or "").lower()
            product_key = self._detect_product(lowered)

            if not product_key:
                return (
                    "I can check your eligibility for personal loans, home loans, "
                    "credit cards, term deposits, and savings accounts. "
                    "Please specify which product you are interested in.\n\n"
                    f"{_DISCLAIMER}"
                )

            return self._check(product_key)

        except Exception as exc:  # noqa: BLE001
            logger.error("EligibilityAgent: unexpected error type=%s", type(exc).__name__)
            return "Unable to check eligibility at this time. Please contact us for assistance."

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _detect_product(self, text: str) -> str | None:
        for keywords, key in _KEYWORD_MAP:
            for kw in keywords:
                if kw in text:
                    return key
        return None

    def _check(self, product_key: str) -> str:
        user = _DEMO_USER
        rules = _RULES[product_key]
        failures: list[str] = []
        passes: list[str] = []

        product_label = product_key.replace("_", " ").title()

        # --- Evaluate each rule ---
        if "min_age" in rules:
            if user["age"] >= rules["min_age"]:
                passes.append(f"Age requirement met (min {rules['min_age']} years)")
            else:
                failures.append(f"Age below minimum requirement of {rules['min_age']} years")

        if "min_income" in rules:
            if user["annual_income"] >= rules["min_income"]:
                passes.append(
                    f"Income requirement met (min AUD {rules['min_income']:,} p.a.)"
                )
            else:
                failures.append(
                    f"Annual income below minimum of AUD {rules['min_income']:,}"
                )

        if "no_defaults" in rules and rules["no_defaults"]:
            if not user["has_defaults"]:
                passes.append("No credit defaults on record")
            else:
                failures.append("Credit defaults detected — disqualified for this product")

        if "no_bankruptcies" in rules and rules["no_bankruptcies"]:
            if not user["has_bankruptcy"]:
                passes.append("No bankruptcy history on record")
            else:
                failures.append("Bankruptcy history detected — disqualified for this product")

        if "min_deposit_pct" in rules:
            # Simplified: check deposit against a representative property value
            representative_value = 500000
            required_deposit = representative_value * rules["min_deposit_pct"] / 100
            if user["deposit_available"] >= required_deposit:
                passes.append(
                    f"Deposit available (AUD {user['deposit_available']:,}) meets minimum "
                    f"{rules['min_deposit_pct']}% deposit requirement"
                )
            else:
                failures.append(
                    f"Insufficient deposit — minimum {rules['min_deposit_pct']}% "
                    f"(AUD {required_deposit:,.0f}) required for a AUD {representative_value:,} property"
                )

        if "min_amount" in rules:
            passes.append(
                f"Minimum deposit amount is AUD {rules['min_amount']:,} — no income restriction applies"
            )

        # --- Format result ---
        if failures:
            result_line = f"Eligibility for {product_label}: NOT MET"
            body_lines = [f"  ✗ {f}" for f in failures] + [f"  ✓ {p}" for p in passes]
            alternative = self._suggest_alternative(product_key)
            return (
                f"{result_line}\n\n"
                + "\n".join(body_lines)
                + (f"\n\nAlternative: {alternative}" if alternative else "")
                + f"\n\n{_DISCLAIMER}"
            )
        else:
            result_line = f"Eligibility for {product_label}: MEETS CRITERIA"
            body_lines = [f"  ✓ {p}" for p in passes]
            return (
                f"{result_line}\n\n"
                + "\n".join(body_lines)
                + f"\n\n{_DISCLAIMER}"
            )

    def _suggest_alternative(self, product_key: str) -> str | None:
        alternatives = {
            "home_loan": "Consider a Term Deposit or High Interest Savings Account to build your deposit.",
            "personal_loan": "A Basic Credit Card may be available as an alternative for smaller amounts.",
            "credit_card": "An Everyday Savings Account has no income restrictions.",
            "term_deposit": None,
            "savings_account": None,
        }
        return alternatives.get(product_key)
