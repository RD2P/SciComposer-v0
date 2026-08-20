import json
from pathlib import Path
from typing import Any, Optional, cast
from schemas.schemas import WorkflowPlan

from ollama import Client


class PlannerAgent:
    def __init__(
        self,
        model: str = "qwen3.5:9b",
        client: Optional[Client] = None,
        host: Optional[str] = None,
    ) -> None:
        self.model = model
        self._client = client if client is not None else (Client(host=host) if host else Client())

        self._prompt_path = (
            Path(__file__).resolve().parent.parent
            / "prompts"
            / "planner.md"
        )
        self._system_prompt = self._prompt_path.read_text(encoding="utf-8")

    def plan(self, user_request: str) -> WorkflowPlan:
        messages = [
            {
                "role": "system",
                "content": self._system_prompt,
            },
            {
                "role": "user",
                "content": user_request,
            },
        ]

        try:
            response = self._client.chat(
                model=self.model,
                messages=messages,
                format="json",
            )

            content = response["message"]["content"]
            raw_plan = json.loads(content)

            if not isinstance(raw_plan, dict):
                raise ValueError("Planner output is not a JSON object")

            self._validate_plan(raw_plan)

            return cast(WorkflowPlan, raw_plan)

        except Exception as e:
            print(f"Planner error: {e}")

            return {
                "goal": user_request,
                "stages": [],
            }

    @staticmethod
    def _validate_plan(plan: dict[str, Any]) -> None:
        if not isinstance(plan.get("goal"), str):
            raise ValueError("Planner goal must be a string")

        stages = plan.get("stages")

        if not isinstance(stages, list):
            raise ValueError("Planner stages must be a list")

        for stage in stages:
            if not isinstance(stage, dict):
                raise ValueError("Each stage must be an object")

            if not isinstance(stage.get("name"), str):
                raise ValueError("Stage name must be a string")

            if not isinstance(stage.get("description"), str):
                raise ValueError("Stage description must be a string")