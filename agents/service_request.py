# agents/service_request.py
# Purpose: Prepares and handles customer service requests or ticket creations.

class ServiceRequestAgent:
    """Agent that handles service requests, formatting them for backend logging and downstream systems."""

    def run(self, input: str) -> str:
        """Run the service request agent on the input string."""
        return f"ServiceRequest processed: {input}"
