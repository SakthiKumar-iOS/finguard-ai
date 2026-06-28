# tests/test_agents.py
# Purpose: Test various agents' functionality.

def test_other_agents_stubs():
    """Verify that all other agents stubs run correctly."""
    from agents.transaction_analyst import TransactionAnalystAgent
    from agents.product_query import ProductQueryAgent
    from agents.eligibility import EligibilityAgent
    from agents.service_request import ServiceRequestAgent
    from agents.audit_compliance import AuditComplianceAgent

    assert "TransactionAnalyst" in TransactionAnalystAgent().run("x")
    assert "ProductQuery" in ProductQueryAgent().run("x")
    assert "Eligibility" in EligibilityAgent().run("x")
    assert "ServiceRequest" in ServiceRequestAgent().run("x")
    assert "AuditCompliance" in AuditComplianceAgent().run("x")
