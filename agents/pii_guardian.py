# agents/pii_guardian.py
# Purpose: Security gateway. Every input passes through this agent
#          before reaching any specialist agent.

import logging
from typing import Optional

from utils.pii_redactor import redact
from utils.prompt_guard import scan

logger = logging.getLogger(__name__)

_MAX_INPUT_LENGTH = 2000

_BLOCKED_RESPONSE = {
    "status": "blocked",
    "safe_text": "",
    "entities_found": [],
    "threat": None,
    "audit": {
        "input_length": 0,
        "entity_count": 0,
        "was_truncated": False,
        "threat_detected": True,
    },
}


class PIIGuardianAgent:
    """Security gateway. Every input passes through this agent
    before reaching any specialist agent."""

    def run(self, input: str) -> dict:  # noqa: A002
        """Run the PII Guardian security pipeline on *input*.

        Pipeline order:
            1. Validate input type and length (max 2000 chars)
            2. Run prompt_guard.scan() — block immediately if unsafe
            3. Run pii_redactor.redact() on validated input
            4. Return structured response dict

        Returns:
            {
                "status": "blocked" | "redacted" | "clean",
                "safe_text": str,
                "entities_found": list,
                "threat": dict or None,
                "audit": {
                    "input_length": int,
                    "entity_count": int,
                    "was_truncated": bool,
                    "threat_detected": bool,
                }
            }

        Never raises unhandled exceptions — all errors are returned as
        a blocked status response.
        """
        try:
            # ------------------------------------------------------------------
            # Step 1: Validate input type and length
            # ------------------------------------------------------------------
            if input is None or not isinstance(input, str):
                logger.warning("PIIGuardian: invalid input type=%s", type(input).__name__)
                return {
                    **_BLOCKED_RESPONSE,
                    "audit": {
                        "input_length": 0,
                        "entity_count": 0,
                        "was_truncated": False,
                        "threat_detected": True,
                    },
                }

            input_length = len(input)
            was_truncated = input_length > _MAX_INPUT_LENGTH
            validated_input = input[:_MAX_INPUT_LENGTH]

            # ------------------------------------------------------------------
            # Step 2: Prompt-injection / abuse scan — block immediately if unsafe
            # ------------------------------------------------------------------
            guard_result = scan(validated_input)

            if not guard_result["is_safe"]:
                logger.warning(
                    "PIIGuardian: blocking input — threat_type=%s",
                    guard_result.get("threat_type"),
                )
                return {
                    "status": "blocked",
                    "safe_text": "",
                    "entities_found": [],
                    "threat": guard_result,
                    "audit": {
                        "input_length": input_length,
                        "entity_count": 0,
                        "was_truncated": was_truncated,
                        "threat_detected": True,
                    },
                }

            # ------------------------------------------------------------------
            # Step 3: PII detection and redaction
            # ------------------------------------------------------------------
            redact_result = redact(validated_input)

            found_entities: list = redact_result.get("found_entities", [])
            entity_count = len(found_entities)
            redacted_text: str = redact_result.get("redacted", validated_input)
            pii_is_safe: bool = redact_result.get("is_safe", True)

            # ------------------------------------------------------------------
            # Step 4: Build and return structured response
            # ------------------------------------------------------------------
            if not pii_is_safe:
                status = "redacted"
                safe_text = redacted_text
            else:
                status = "clean"
                safe_text = validated_input

            return {
                "status": status,
                "safe_text": safe_text,
                "entities_found": found_entities,
                "threat": None,
                "audit": {
                    "input_length": input_length,
                    "entity_count": entity_count,
                    "was_truncated": was_truncated,
                    "threat_detected": False,
                },
            }

        except Exception as exc:  # noqa: BLE001
            # Never raise — return blocked status for any unexpected error
            logger.error("PIIGuardian: unexpected exception caught: %s", type(exc).__name__)
            return {
                "status": "blocked",
                "safe_text": "",
                "entities_found": [],
                "threat": {"error": type(exc).__name__},
                "audit": {
                    "input_length": 0,
                    "entity_count": 0,
                    "was_truncated": False,
                    "threat_detected": True,
                },
            }
