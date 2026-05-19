from services.controller import LigentController
from services.schemas import (
    AgentResultSummary,
    ConflictSummary,
    DecisionSummary,
    OllamaPlanRequest,
    RunDetailResponse,
    RunPreviewRequest,
    RunPreviewResponse,
    TaskDetail,
)
from state.store import ProjectStore


def create_run_preview(payload: RunPreviewRequest) -> RunPreviewResponse:
    return LigentController().run(payload.goal)


def create_ollama_plan(payload: OllamaPlanRequest) -> RunPreviewResponse:
    return LigentController().run_ollama_planning(payload.goal, model=payload.model)


def get_run_detail(
    run_id: str,
    store: ProjectStore | None = None,
) -> RunDetailResponse | None:
    project_store = store or LigentController().store
    run = project_store.get_run(run_id)
    if run is None:
        return None

    messages_by_task = {
        message.task_id: message
        for message in project_store.list_agent_messages(run_id)
    }
    tasks = []
    for task in project_store.list_tasks(run_id):
        results = [
            AgentResultSummary(
                agent=result.agent,
                result=result.result,
                evidence=result.evidence,
                confidence=result.confidence,
            )
            for result in project_store.list_agent_results(task.id)
        ]
        message = messages_by_task.get(task.id)
        tasks.append(
            TaskDetail(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                assignedAgent=task.assigned_agent,
                instructions=message.instructions if message else "",
                results=results,
            )
        )

    decisions = [
        DecisionSummary(
            id=decision.id,
            summary=decision.summary,
            reason=decision.reason,
            chosenOption=decision.chosen_option,
        )
        for decision in project_store.list_decisions(run_id)
    ]
    conflicts = [
        ConflictSummary(
            id=conflict.id,
            summary=conflict.summary,
            status=conflict.status,
        )
        for conflict in project_store.list_conflicts(run_id)
    ]

    return RunDetailResponse(
        runId=run.id,
        status=run.status,
        goal=run.goal,
        finalSummary=_build_final_summary(
            task_count=len(tasks),
            decision_count=len(decisions),
            conflict_count=len(conflicts),
        ),
        tasks=tasks,
        decisions=decisions,
        conflicts=conflicts,
        createdAt=run.created_at,
    )


def _build_final_summary(
    *,
    task_count: int,
    decision_count: int,
    conflict_count: int,
) -> str:
    return (
        f"Ligent persisted {task_count} task records, {decision_count} decisions, "
        f"and {conflict_count} open conflicts. This demo records what happened, "
        "what each agent returned, and what remains for the next controller step."
    )
