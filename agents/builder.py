from pathlib import Path
import json

from ollama import Client


class BuilderAgent:
    def __init__(
        self,
        client: Client,
        model: str = "qwen3.5:9b",
        prompt_path: str | Path | None = None,
    ):
        self.client = client
        self.model = model

        self._prompt_path = (
            Path(prompt_path)
            if prompt_path is not None
            else Path(__file__).resolve().parent.parent / "prompts" / "builder.md"
        )
        self.system_prompt = self._prompt_path.read_text(encoding="utf-8")

    def build(
        self,
        user_request: str,
        workflow_plan: dict,
        candidate_tools: list[dict],
        workflow_examples: list[dict],
    ) -> dict:

        context = {
            "user_request": user_request,
            "workflow_plan": workflow_plan,
            "candidate_tools": candidate_tools,
            "workflow_examples": workflow_examples,
        }

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt,
                },
                {
                    "role": "user",
                    "content": json.dumps(context, indent=2),
                },
            ],
            options={
                "temperature": 0,
            },
        )

        content = response["message"]["content"]

        return json.loads(content)