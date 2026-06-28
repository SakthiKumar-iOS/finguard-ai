# tests/test_agents.py
import pytest
from agents.transaction_analyst import TransactionAnalystAgent
from agents.product_query import ProductQueryAgent
from agents.eligibility import EligibilityAgent
from agents.service_request import ServiceRequestAgent
from agents.audit_compliance import AuditComplianceAgent

def test_transaction_analyst():
    response = TransactionAnalystAgent().run("Show my transactions")
    assert isinstance(response, str)
    assert len(response) > 0

def test_transaction_unusual():
    response = TransactionAnalystAgent().run("Show unusual spending")
    assert isinstance(response, str)
    assert len(response) > 0

def test_product_query():
    response = ProductQueryAgent().run("Tell me about savings accounts")
    assert "indicative" in response.lower()

def test_product_disclaimer():
    response = ProductQueryAgent().run("What loans do you offer?")
    assert "indicative" in response.lower()

def test_eligibility_pass():
    response = EligibilityAgent().run("Am I eligible for a home loan?")
    assert isinstance(response, str)
    assert len(response) > 0
    assert "assessment" in response.lower()

def test_service_request_reference():
    response = ServiceRequestAgent().run("I want to dispute a charge")
    assert "SR" in response

def test_service_demo_disclaimer():
    response = ServiceRequestAgent().run("Please freeze my card")
    assert "demo" in response.lower()

def test_audit_compliance():
    response = AuditComplianceAgent().run("Show audit log")
    assert isinstance(response, str)
    assert len(response) > 0

def test_audit_compliance_report():
    response = AuditComplianceAgent().run("Show compliance report")
    assert "PII Guardian" in response
