from app.agent.router import AgentRouter


def test_agent_router_classification():
    # Test Ship 30 for 30 classification
    ship30_res = AgentRouter.classify_intent("Please write a Ship 30 for 30 essay on marketplace cold start")
    assert ship30_res.intent == "ship30"

    # Test Artifact classification
    artifact_res = AgentRouter.classify_intent("Build a PMF calculator widget in HTML")
    assert artifact_res.intent == "artifact"

    # Test General Q&A classification
    qa_res = AgentRouter.classify_intent("How did Lenny define retention curves?")
    assert qa_res.intent == "qa"

    # Test Explicit Override
    override_res = AgentRouter.classify_intent("Any prompt", skill_override="ship30")
    assert override_res.intent == "ship30"

