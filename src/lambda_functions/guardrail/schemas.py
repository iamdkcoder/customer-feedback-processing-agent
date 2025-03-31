from pydantic import BaseModel, Field

class GuardrailOutput(BaseModel):
    """
    Guardrail output schema.
    """
    is_safe: bool = Field(description="Whether the message is safe to proceed with.")
    reason: str = Field(description="The reason for the guardrail check.")

