from enum import StrEnum


class AgentRole(StrEnum):
    PLANNER = "planner"
    DESIGN = "design"
    IMPLEMENT = "implement"
    QA = "qa"
    DEVOPS = "devops"
    DOCUMENTATION = "documentation"

