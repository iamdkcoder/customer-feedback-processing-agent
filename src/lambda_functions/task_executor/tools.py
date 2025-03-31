from agents import Agent

from prompts import (
    SENTIMENT_ANALYSIS_INSTRUCTIONS,
    TOPIC_CATEGORIZATION_INSTRUCTIONS,
    KEYWORD_CONTEXTUALIZATION_INSTRUCTIONS,
    SUMMARY_GENERATION_INSTRUCTIONS,
    TASK_PLANNER_INSTRUCTIONS,
)
from schemas import (
    SentimentAnalysisOutput,
    TopicCategorizationOutput,
    KeywordContextualizationOutput,
    SummaryGenerationOutput,
    TaskPlannerOutput,
)


sentiment_analysis_tool = Agent(
    name="Sentiment Analysis Tool",
    model="gpt-4o-mini",
    instructions=SENTIMENT_ANALYSIS_INSTRUCTIONS,
    output_type=SentimentAnalysisOutput,
    tools=[],
)

topic_categorization_tool = Agent(
    name="Topic Categorization Tool",
    model="gpt-4o-mini",
    instructions=TOPIC_CATEGORIZATION_INSTRUCTIONS,
    output_type=TopicCategorizationOutput,
    tools=[],
)

keyword_contextualization_tool = Agent(
    name="Keyword Contextualization Tool",
    model="gpt-4o-mini",
    instructions=KEYWORD_CONTEXTUALIZATION_INSTRUCTIONS,
    output_type=KeywordContextualizationOutput,
    tools=[],
)


summary_generation_tool = Agent(
    name="Summary Generation Tool",
    model="gpt-4o-mini",
    instructions=SUMMARY_GENERATION_INSTRUCTIONS,
    output_type=SummaryGenerationOutput,
    tools=[],
)


task_planner_tool = Agent(
    name="Task Planner Tool",
    model="gpt-4o-mini",
    instructions=TASK_PLANNER_INSTRUCTIONS,
    output_type=TaskPlannerOutput,
)
