from pydantic import BaseModel, Field


class AgentWorkOutput(BaseModel):
    summary: str = Field(min_length=1, max_length=1200)
    recommendation: str = Field(min_length=1, max_length=2000)
    status: str = Field(default="completed", min_length=1, max_length=32)
    evidence: list[str] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0, le=1)


AGENT_OUTPUT_SCHEMA_HINT = """
{
  "summary": "short agent summary",
  "recommendation": "specific recommendation or result",
  "status": "completed",
  "evidence": ["short evidence item"],
  "confidence": 0.0
}
""".strip()
