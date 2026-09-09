from typing import Literal
from pydantic import BaseModel, Field


class IntentClassification(BaseModel):
    intent: Literal["qa", "ship30", "artifact", "unsupported"] = Field(
        description="Classified skill routing intent"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    topic: str = Field(default="", description="Extracted core growth/product topic")


class AgentRouter:
    """
    Deterministic Agent Router responsible for intent classification and skill dispatching.
    """

    @classmethod
    def classify_intent(cls, user_message: str, skill_override: str = None) -> IntentClassification:
        """
        Classify intent based on explicit skill overrides or natural language heuristics.
        """
        if skill_override in ["qa", "ship30", "artifact", "unsupported"]:
            return IntentClassification(intent=skill_override, confidence=1.0, topic=user_message)

        lower_msg = user_message.lower()

        # Check for Ship 30 for 30 intent
        ship30_keywords = [
            "ship 30", "ship30", "write an essay", "atomic essay", "long form essay",
            "write a post", "write an article", "create a post", "create an essay",
            "turn those ideas into a post", "turn these ideas into a post",
            "turn those ideas into an essay", "turn these ideas into an essay",
            "turn into a ship 30", "write a ship 30 post", "ship 30 for 30",
            "editorial piece", "write an article about",
        ]
        if any(keyword in lower_msg for keyword in ship30_keywords):
            return IntentClassification(intent="ship30", confidence=0.95, topic=user_message)

        # Check for Artifact generation intent
        if any(keyword in lower_msg for keyword in ["create artifact", "generate artifact", "build a calculator", "pmf calculator", "html widget", "calculator widget", "create a table", "pricing matrix"]):
            return IntentClassification(intent="artifact", confidence=0.95, topic=user_message)

        # Default grounded Q&A
        return IntentClassification(intent="qa", confidence=0.90, topic=user_message)


router = AgentRouter()

