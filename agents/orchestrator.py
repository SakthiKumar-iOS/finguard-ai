# agents/orchestrator.py
# Purpose: Central router. Screens input via PII Guardian then
#          routes to specialist agents based on detected intent.

import logging

from agents.pii_guardian import PIIGuardianAgent
from agents.transaction_analyst import TransactionAnalystAgent
from agents.product_query import ProductQueryAgent
from agents.eligibility import EligibilityAgent
from agents.service_request import ServiceRequestAgent
from agents.audit_compliance import AuditComplianceAgent

logger = logging.getLogger(__name__)

_MAX_INPUT_LENGTH = 2000
_MAX_RESPONSE_LENGTH = 500

_SECURITY_REFUSAL = (
    "Your request could not be processed due to a security policy. "
    "Please rephrase and try again."
)
_CLARIFICATION_MSG = (
    "I can help with transactions, products, eligibility, "
    "or service requests. Could you clarify your request?"
)
_ERROR_MSG = "Unable to process your request. Please try again."

# ---------------------------------------------------------------------------
# Intent keyword map — ordered: more-specific first
# ---------------------------------------------------------------------------
_INTENT_KEYWORDS: list[tuple[str, list[str]]] = [
    ("audit", [
        "audit", "compliance", "activity", "session", "record",
    ]),
    ("eligibility", [
        "eligible", "eligibility", "qualify", "qualify for",
        "apply", "application", "approve", "approval", "limit", "criteria",
        "income", "credit score", "borrow", "afford",
    ]),
    ("service", [
        "dispute", "complaint", "request", "freeze", "block",
        "unblock", "report", "lost", "stolen", "change", "update",
        "callback", "help", "support", "issue", "problem", "cancel",
    ]),
    ("product", [
        "product", "account", "savings", "loan", "mortgage",
        "card", "interest", "rate", "fee", "offer", "plan", "insurance",
        "investment", "term deposit", "fixed", "variable",
    ]),
    ("transaction", [
        "transaction", "spending", "spent", "balance",
        "statement", "history", "unusual", "suspicious", "charge",
        "debit", "credit", "payment", "transfer", "withdraw", "deposit",
    ]),
]


class OrchestratorAgent:
    """Central router. Screens input via PII Guardian then
    routes to specialist agents based on detected intent."""

    def __init__(self) -> None:
        # All agents instantiated once at init — no shared mutable state
        self._pii_guardian = PIIGuardianAgent()
        self._transaction_analyst = TransactionAnalystAgent()
        self._product_query = ProductQueryAgent()
        self._eligibility = EligibilityAgent()
        self._service_request = ServiceRequestAgent()
        self._audit_compliance = AuditComplianceAgent()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, input: str) -> str:  # noqa: A002
        """Screen input through PII Guardian then route to the correct
        specialist agent.  Returns a plain-text response string.

        Pipeline:
            1. Validate input (type, strip, max 2000 chars)
            2. PIIGuardianAgent.run() — block if unsafe
            3. Detect intent from safe_text
            4. Route to specialist agent
            5. Validate and return response
        """
        try:
            # ----------------------------------------------------------
            # Step 1: Validate input
            # ----------------------------------------------------------
            if input is None or not isinstance(input, str):
                logger.debug("OrchestratorAgent: non-string input type=%s", type(input).__name__)
                return _CLARIFICATION_MSG

            stripped = input.strip()
            if not stripped:
                return _CLARIFICATION_MSG

            # Truncate silently
            validated = stripped[:_MAX_INPUT_LENGTH]

            # ----------------------------------------------------------
            # Step 2: PII Guardian screen
            # ----------------------------------------------------------
            guardian_result: dict = self._pii_guardian.run(validated)
            status: str = guardian_result.get("status", "blocked")

            if status == "blocked":
                logger.warning("OrchestratorAgent: input blocked by PII Guardian")
                return _SECURITY_REFUSAL

            # Step 4 rule: always use safe_text for all further steps
            safe_text: str = guardian_result.get("safe_text", "")
            if not safe_text:
                # Guardian returned clean but with empty safe_text — use validated
                safe_text = validated

            # ----------------------------------------------------------
            # Step 5: Detect intent
            # ----------------------------------------------------------
            intent = self._detect_intent(safe_text)
            logger.debug("OrchestratorAgent: intent=%s", intent)

            # ----------------------------------------------------------
            # Step 6: Route to specialist agent
            # ----------------------------------------------------------
            response = self._route(intent, safe_text)

            # ----------------------------------------------------------
            # Step 7: Validate specialist agent response
            # ----------------------------------------------------------
            if not response or not isinstance(response, str) or not response.strip():
                return _CLARIFICATION_MSG

            # Enforce max response length
            return response[:_MAX_RESPONSE_LENGTH]

        except Exception as exc:  # noqa: BLE001
            # Never expose internal details
            logger.error("OrchestratorAgent: unexpected exception type=%s", type(exc).__name__)
            return _ERROR_MSG

    # ------------------------------------------------------------------
    # Intent detection
    # ------------------------------------------------------------------

    def _detect_intent(self, text: str) -> str:
        """Classify *text* into an intent label using keyword matching only.

        Returns one of: "transaction", "product", "eligibility",
                        "service", "audit", "unknown".
        """
        lowered = text.lower()
        for intent, keywords in _INTENT_KEYWORDS:
            for kw in keywords:
                if kw in lowered:
                    return intent
        return "unknown"

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def _route(self, intent: str, safe_text: str) -> str:
        """Route *safe_text* to the correct specialist agent based on *intent*.

        Never passes original user input — only safe_text from PII Guardian.
        """
        try:
            if intent == "transaction":
                return self._transaction_analyst.run(safe_text)
            elif intent == "product":
                return self._product_query.run(safe_text)
            elif intent == "eligibility":
                return self._eligibility.run(safe_text)
            elif intent == "service":
                return self._service_request.run(safe_text)
            elif intent == "audit":
                return self._audit_compliance.run(safe_text)
            else:
                # "unknown" — return clarification
                return _CLARIFICATION_MSG
        except Exception as exc:  # noqa: BLE001
            # Log intent only — never log safe_text or stack trace to user
            logger.error(
                "OrchestratorAgent: specialist agent raised exception intent=%s type=%s",
                intent,
                type(exc).__name__,
            )
            return _ERROR_MSG
