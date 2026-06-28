# tests/test_pii_guardian.py
# Purpose: Test PIIGuardianAgent functionality.

def test_pii_guardian_stub():
    """Verify that the pii guardian agent stub runs correctly."""
    from agents.pii_guardian import PIIGuardianAgent
    agent = PIIGuardianAgent()
    res = agent.run("test input")
    assert "PIIGuardian processed" in res
