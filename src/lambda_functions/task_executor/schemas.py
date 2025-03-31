from pydantic import BaseModel, Field
from typing import Literal, List, Any


class SentimentAnalysisOutput(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"] = Field(
        description="The sentiment of the user's message"
    )


class TopicCategorizationOutput(BaseModel):
    topic: Literal["shipping", "returns", "payment", "account", "support", "other"] = (
        Field(description="The topic of the user's message")
    )


class Keyword(BaseModel):
    term: str = Field(description="The keyword in the user's message")
    relevance_score: int = Field(
        description="The relevance score of the keyword to the user's message (0-100)"
    )
    context: str = Field(description="The context of the keyword in the user's message")


class KeywordContextualizationOutput(BaseModel):
    keywords: List[Keyword] = Field(description="The keywords in the user's message")


class SummaryGenerationOutput(BaseModel):
    summary: str = Field(description="The summary of the user's message")
    action_items: list[str] = Field(description="The action items from the feedback")


class TaskPlannerOutput(BaseModel):
    use_tools: list[
        Literal[
            "sentiment_analysis",
            "topic_categorization",
            "keyword_contextualization",
            "summary_generation",
        ]
    ] = Field(description="The tools to be executed")
    message: str = Field(description="The message to be displayed to the user")
