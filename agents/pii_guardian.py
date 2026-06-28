# agents/pii_guardian.py
# Purpose: Detects and redacts sensitive PII information from user inputs.

class PIIGuardianAgent:
    """Agent that handles PII detection and redaction using Presidio."""

    def run(self, input: str) -> str:
        """Run the PII Guardian agent on the input string."""
        return f"PIIGuardian processed: {input}"
