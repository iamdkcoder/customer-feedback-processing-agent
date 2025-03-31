from agents import Agent, ModelSettings

from prompts import GUARDRAIL_INSTRUCTIONS
from schemas import GuardrailOutput


guardrail_tool = Agent(
    name="Guardrail Tool",
    instructions=GUARDRAIL_INSTRUCTIONS,
    output_type=GuardrailOutput,
    model="gpt-4o-mini",
    model_settings=ModelSettings(temperature=0.0),
)
