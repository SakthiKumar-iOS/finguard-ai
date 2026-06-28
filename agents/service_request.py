# agents/service_request.py
# Purpose: Prepares and handles customer service requests or ticket creations.

import logging
import random

logger = logging.getLogger(__name__)

_DEMO_DISCLAIMER = "This is a demo system. No real actions have been taken."


def _ref() -> str:
    """Generate a synthetic service request reference number."""
    return "SR" + "".join(str(random.randint(0, 9)) for _ in range(8))


class ServiceRequestAgent:
    """Agent that handles service requests, formatting them for backend logging and downstream systems."""

    def run(self, input: str) -> str:  # noqa: A002
        """Handle a service request based on keywords in *input*."""
        try:
            lowered = (input or "").lower()

            if any(kw in lowered for kw in ["dispute", "chargeback", "unauthorised", "unauthorized"]):
                return self._dispute()

            if any(kw in lowered for kw in ["freeze", "block card", "block my card"]):
                return self._freeze_card()

            if any(kw in lowered for kw in ["lost", "stolen"]):
                return self._lost_stolen()

            if any(kw in lowered for kw in ["callback", "call me", "contact me", "call back"]):
                return self._callback()

            if any(kw in lowered for kw in ["complaint", "complain", "unhappy", "dissatisfied"]):
                return self._complaint()

            if any(kw in lowered for kw in ["cancel", "close account", "close my"]):
                return self._cancel()

            # Default acknowledgement
            return self._default()

        except Exception as exc:  # noqa: BLE001
            logger.error("ServiceRequestAgent: unexpected error type=%s", type(exc).__name__)
            return (
                "We have received your request and our team will be in touch shortly. "
                f"{_DEMO_DISCLAIMER}"
            )

    # ------------------------------------------------------------------
    # Request handlers
    # ------------------------------------------------------------------

    def _dispute(self) -> str:
        ref = _ref()
        return (
            f"Thank you for raising a dispute. Your case has been logged with reference {ref}.\n\n"
            "Our disputes team will review the transaction(s) in question and contact you "
            "within 5 business days. If this is an urgent matter, please call us directly.\n\n"
            f"{_DEMO_DISCLAIMER}"
        )

    def _freeze_card(self) -> str:
        ref = _ref()
        return (
            f"Understood. A card block request for your card ending ****1234 has been "
            f"acknowledged with reference {ref}.\n\n"
            "Your card will be reviewed by our security team. You can manage your card "
            "status at any time via online banking.\n\n"
            f"{_DEMO_DISCLAIMER}"
        )

    def _lost_stolen(self) -> str:
        ref = _ref()
        return (
            f"We are sorry to hear your card has been lost or stolen. "
            f"Your report reference is {ref}.\n\n"
            "Please call us immediately on 1800-FINGUARD (1800-346-482) to arrange "
            "a replacement card and to review any unauthorised transactions.\n\n"
            f"{_DEMO_DISCLAIMER}"
        )

    def _callback(self) -> str:
        ref = _ref()
        return (
            f"Your callback request has been registered with reference {ref}.\n\n"
            "A member of our team will contact you within 24 business hours. "
            "If your matter is urgent, please call us on 1800-FINGUARD.\n\n"
            f"{_DEMO_DISCLAIMER}"
        )

    def _complaint(self) -> str:
        ref = _ref()
        return (
            f"We sincerely apologise for the experience you have had. "
            f"Your complaint has been registered with reference {ref}.\n\n"
            "A dedicated team member will review your complaint and respond within "
            "5 business days in line with our complaints resolution policy.\n\n"
            f"{_DEMO_DISCLAIMER}"
        )

    def _cancel(self) -> str:
        ref = _ref()
        return (
            f"Thank you for letting us know. Your request reference is {ref}.\n\n"
            "Account closure and cancellation requests must be processed in person at "
            "a branch with valid identification. Please visit your nearest FinGuard branch "
            "to complete this process.\n\n"
            f"{_DEMO_DISCLAIMER}"
        )

    def _default(self) -> str:
        ref = _ref()
        return (
            f"Thank you for your request. It has been logged with reference {ref}.\n\n"
            "Our team will review your request and be in touch shortly. "
            "For immediate assistance, please call 1800-FINGUARD or visit your nearest branch.\n\n"
            f"{_DEMO_DISCLAIMER}"
        )
