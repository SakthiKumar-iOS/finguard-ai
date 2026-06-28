# agents/product_query.py
# Purpose: Answers queries about financial products by querying a knowledge base.

class ProductQueryAgent:
    """Agent that queries the products database to provide information about financial products."""

    def run(self, input: str) -> str:
        """Run the product query agent on the input string."""
        return f"ProductQuery processed: {input}"
