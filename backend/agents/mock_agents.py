from state.models import AgentMessage, AgentResult, TaskState


class MockAgent:
    def run(self, message: AgentMessage, task: TaskState) -> AgentResult:
        if task.assigned_agent is None:
            raise ValueError("MockAgent requires an assigned task.")

        return AgentResult(
            id=f"result_{task.id}",
            message_id=message.id,
            task_id=task.id,
            agent=task.assigned_agent,
            result={
                "title": task.title,
                "recommendation": self._recommendation(task),
                "status": "completed",
            },
            evidence=[
                f"task:{task.id}",
                f"agent:{task.assigned_agent.value}",
            ],
            confidence=0.75,
        )

    @staticmethod
    def _recommendation(task: TaskState) -> str:
        role = task.assigned_agent.value if task.assigned_agent else "agent"
        return f"{role} completed deterministic mock work for: {task.description}"


class MockRoleAgentExecutor:
    def __init__(self, mock_agent: MockAgent | None = None) -> None:
        self.mock_agent = mock_agent or MockAgent()

    def execute(
        self,
        *,
        task: TaskState,
        message: AgentMessage,
        goal: str,
    ) -> AgentResult:
        return self.mock_agent.run(message, task)
