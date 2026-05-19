from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

from google.adk import Runner
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import ValidationError

from agents.adk_models import AGENT_OUTPUT_SCHEMA_HINT, AgentWorkOutput
from agents.roles import AgentRole
from state.models import AgentMessage, AgentResult, TaskState


DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "gemma4:e2b"


class RoleAgentExecutor(Protocol):
    def execute(
        self,
        *,
        task: TaskState,
        message: AgentMessage,
        goal: str,
    ) -> AgentResult:
        """Run a scoped agent turn and return a validated result."""


@dataclass(frozen=True)
class AdkRoleAgentExecutor:
    model_name: str = DEFAULT_OLLAMA_MODEL
    base_url: str = DEFAULT_OLLAMA_BASE_URL
    user_id: str = "ligent-controller"
    app_name: str = "ligent"

    def execute(
        self,
        *,
        task: TaskState,
        message: AgentMessage,
        goal: str,
    ) -> AgentResult:
        if task.assigned_agent is None:
            raise ValueError("task must have an assigned agent")

        agent = build_role_agent(
            role=task.assigned_agent,
            model_name=self.model_name,
            base_url=self.base_url,
        )
        runner = Runner(
            agent=agent,
            session_service=InMemorySessionService(),
            app_name=self.app_name,
        )
        session_id = f"session_{task.id}"
        adk_prompt = build_agent_prompt(task=task, message=message, goal=goal)
        final_text = asyncio.run(
            self._run_agent(
                runner=runner,
                user_id=self.user_id,
                session_id=session_id,
                prompt=adk_prompt,
            )
        )
        output = parse_agent_output(final_text)

        return AgentResult(
            id=f"result_{task.id}",
            message_id=message.id,
            task_id=task.id,
            agent=task.assigned_agent,
            result=output.model_dump(),
            evidence=[
                *output.evidence,
                f"provider=adk",
                f"model={self.model_name}",
            ],
            confidence=output.confidence,
        )

    async def _run_agent(
        self,
        *,
        runner: Runner,
        user_id: str,
        session_id: str,
        prompt: str,
    ) -> str:
        await runner.session_service.create_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id,
        )
        try:
            final_text = ""
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(parts=[types.Part(text=prompt)]),
            ):
                final_text = self._extract_final_text(event)

            if not final_text:
                raise RuntimeError("ADK did not return a final agent response.")
            return final_text
        finally:
            await runner.close()

    @staticmethod
    def _extract_final_text(event: object) -> str:
        content = getattr(event, "content", None)
        if content is None:
            return ""

        parts = getattr(content, "parts", None) or []
        texts = [
            part.text
            for part in parts
            if getattr(part, "text", None)
        ]
        if not texts:
            return ""
        return texts[-1].strip()


@lru_cache(maxsize=1)
def build_role_agent(
    *,
    role: AgentRole,
    model_name: str = DEFAULT_OLLAMA_MODEL,
    base_url: str = DEFAULT_OLLAMA_BASE_URL,
) -> Agent:
    model = LiteLlm(model=f"ollama_chat/{model_name}", api_base=base_url)
    return Agent(
        name=role.value,
        model=model,
        instruction=build_role_instruction(role),
        output_schema=AgentWorkOutput,
    )


def build_role_instruction(role: AgentRole) -> str:
    title = role.value.replace("_", " ").title()
    return (
        f"You are Ligent's {title} agent.\n"
        "Stay local-first, concise, and specific.\n"
        "Return only JSON matching the schema.\n"
        f"Schema:\n{AGENT_OUTPUT_SCHEMA_HINT}\n"
        "Rules:\n"
        "- Keep the summary short.\n"
        "- Keep the recommendation concrete and actionable.\n"
        "- Use confidence between 0 and 1.\n"
        "- Put any supporting points in the evidence list.\n"
    )


def build_agent_prompt(
    *,
    task: TaskState,
    message: AgentMessage,
    goal: str,
) -> str:
    if task.assigned_agent is None:
        raise ValueError("task must have an assigned agent")

    constraints = "\n- ".join(
        message.constraints or ["Return structured output only."]
    )
    expected_output = json.dumps(message.expected_output, indent=2)

    return (
        f"Goal:\n{goal}\n\n"
        f"Agent role:\n{task.assigned_agent.value}\n\n"
        f"Task title:\n{task.title}\n\n"
        f"Task description:\n{task.description}\n\n"
        f"Instructions:\n{message.instructions}\n\n"
        f"Constraints:\n- {constraints}\n\n"
        f"Expected output:\n{expected_output}\n"
        "Return only the JSON object."
    )


def parse_agent_output(raw_text: str) -> AgentWorkOutput:
    json_text = _extract_json_object(raw_text)
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as error:
        raise ValueError("ADK agent output was not valid JSON.") from error

    try:
        return AgentWorkOutput.model_validate(parsed)
    except ValidationError as error:
        raise ValueError("ADK agent output did not match the expected schema.") from error


def _extract_json_object(raw_text: str) -> str:
    fenced = re.search(r"```json\s*(\{.*\})\s*```", raw_text, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()

    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw_text[start : end + 1].strip()

    return raw_text.strip()
