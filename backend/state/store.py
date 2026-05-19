from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, TypeAdapter

from state.models import (
    AgentMessage,
    AgentResult,
    ConflictRecord,
    DecisionRecord,
    ProjectState,
    RunState,
    TaskState,
)

ModelT = TypeVar("ModelT", bound=BaseModel)


SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  data TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  data TEXT NOT NULL,
  FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS agent_messages (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  data TEXT NOT NULL,
  FOREIGN KEY (run_id) REFERENCES runs(id),
  FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS agent_results (
  id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  message_id TEXT NOT NULL,
  data TEXT NOT NULL,
  FOREIGN KEY (task_id) REFERENCES tasks(id),
  FOREIGN KEY (message_id) REFERENCES agent_messages(id)
);

CREATE TABLE IF NOT EXISTS decisions (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  data TEXT NOT NULL,
  FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS conflicts (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  data TEXT NOT NULL,
  FOREIGN KEY (run_id) REFERENCES runs(id)
);
"""


class ProjectStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(SCHEMA)

    def save_project(self, project: ProjectState) -> None:
        self._upsert("projects", project.id, project)

    def get_project(self, project_id: str) -> ProjectState | None:
        return self._get("projects", project_id, ProjectState)

    def save_run(self, run: RunState) -> None:
        self._upsert("runs", run.id, run, {"project_id": run.project_id})

    def get_run(self, run_id: str) -> RunState | None:
        return self._get("runs", run_id, RunState)

    def save_task(self, task: TaskState) -> None:
        self._upsert("tasks", task.id, task, {"run_id": task.run_id})

    def list_tasks(self, run_id: str) -> list[TaskState]:
        return self._list("tasks", "run_id", run_id, TaskState)

    def save_agent_message(self, message: AgentMessage) -> None:
        self._upsert(
            "agent_messages",
            message.id,
            message,
            {"run_id": message.run_id, "task_id": message.task_id},
        )

    def list_agent_messages(self, run_id: str) -> list[AgentMessage]:
        return self._list("agent_messages", "run_id", run_id, AgentMessage)

    def save_agent_result(self, result: AgentResult) -> None:
        self._upsert(
            "agent_results",
            result.id,
            result,
            {"task_id": result.task_id, "message_id": result.message_id},
        )

    def list_agent_results(self, task_id: str) -> list[AgentResult]:
        return self._list("agent_results", "task_id", task_id, AgentResult)

    def save_decision(self, decision: DecisionRecord) -> None:
        self._upsert("decisions", decision.id, decision, {"run_id": decision.run_id})

    def list_decisions(self, run_id: str) -> list[DecisionRecord]:
        return self._list("decisions", "run_id", run_id, DecisionRecord)

    def save_conflict(self, conflict: ConflictRecord) -> None:
        self._upsert("conflicts", conflict.id, conflict, {"run_id": conflict.run_id})

    def list_conflicts(self, run_id: str) -> list[ConflictRecord]:
        return self._list("conflicts", "run_id", run_id, ConflictRecord)

    def _upsert(
        self,
        table: str,
        row_id: str,
        model: BaseModel,
        indexed_values: dict[str, str] | None = None,
    ) -> None:
        indexed_values = indexed_values or {}
        columns = ["id", *indexed_values.keys(), "data"]
        placeholders = ", ".join("?" for _ in columns)
        updates = ", ".join(f"{column}=excluded.{column}" for column in columns[1:])
        values = [
            row_id,
            *indexed_values.values(),
            model.model_dump_json(by_alias=True),
        ]

        with self._connect() as connection:
            connection.execute(
                f"""
                INSERT INTO {table} ({", ".join(columns)})
                VALUES ({placeholders})
                ON CONFLICT(id) DO UPDATE SET {updates}
                """,
                values,
            )

    def _get(
        self,
        table: str,
        row_id: str,
        model_type: type[ModelT],
    ) -> ModelT | None:
        with self._connect() as connection:
            row = connection.execute(
                f"SELECT data FROM {table} WHERE id = ?",
                (row_id,),
            ).fetchone()

        if row is None:
            return None

        return self._parse(row[0], model_type)

    def _list(
        self,
        table: str,
        indexed_column: str,
        indexed_value: str,
        model_type: type[ModelT],
    ) -> list[ModelT]:
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT data FROM {table} WHERE {indexed_column} = ? ORDER BY id",
                (indexed_value,),
            ).fetchall()

        return [self._parse(row[0], model_type) for row in rows]

    @staticmethod
    def _parse(raw_json: str, model_type: type[ModelT]) -> ModelT:
        data: dict[str, Any] = json.loads(raw_json)
        return TypeAdapter(model_type).validate_python(data)
