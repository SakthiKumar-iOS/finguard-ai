# tests/test_orchestrator.py
# Purpose: Test OrchestratorAgent functionality.

def test_orchestrator_stub():
    """Verify that the orchestrator agent stub runs correctly."""
    from agents.orchestrator import OrchestratorAgent
    agent = OrchestratorAgent()
    res = agent.run("test input")
    assert "Orchestrator processed" in res
