from pydantic import BaseModel, Field


class PlanningTaskOutput(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=1200)
    acceptance: list[str] = Field(default_factory=list, max_length=8)


class PlanningOutput(BaseModel):
    summary: str = Field(min_length=1, max_length=1200)
    tasks: list[PlanningTaskOutput] = Field(min_length=1, max_length=8)
    risks: list[str] = Field(default_factory=list, max_length=8)
    next_step: str = Field(min_length=1, max_length=400)
    confidence: float = Field(ge=0, le=1)


PLANNING_SCHEMA_HINT = """
{
  "summary": "short project planning summary",
  "tasks": [
    {
      "title": "short task title",
      "description": "scoped implementation task",
      "acceptance": ["testable acceptance point"]
    }
  ],
  "risks": ["specific risk or permission concern"],
  "next_step": "single next action",
  "confidence": 0.0
}
""".strip()
