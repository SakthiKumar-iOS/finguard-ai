# agents/transaction_analyst.py
# Purpose: Analyzes bank transactions to flag anomalies or explain user spending patterns.

class TransactionAnalystAgent:
    """Agent that performs detailed analysis and verification of transaction records."""

    def run(self, input: str) -> str:
        """Run the transaction analyst agent on the input string."""
        return f"TransactionAnalyst processed: {input}"
