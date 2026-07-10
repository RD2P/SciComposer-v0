import json
from pathlib import Path
from typing import Any, Optional

from ollama import Client


class PlannerAgent:
    def __init__(self, model: str = "qwen3.5:9b", host: Optional[str] = None) -> None:
        self.model = model
        self._client = Client(host=host) if host else Client()
        self._default_stages = ["input_qc", "preprocessing", "analysis", "reporting"]
        self._prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "planner.md"
        self._system_prompt = self._prompt_path.read_text(encoding="utf-8")

    def plan(self, user_request: str) -> dict[str, Any]:
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
            plan = json.loads(content)
            if not isinstance(plan, dict):
                raise ValueError("Planner output is not a JSON object")
        except Exception:
            plan = {
                "goal": user_request,
                "stages": self._default_stages,
            }

        plan.setdefault("goal", user_request)
        plan.setdefault("stages", self._default_stages)
        return plan