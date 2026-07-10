from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExampleWorkflow:
    name: str
    tools: list[str]
    description: str = ""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ExampleWorkflow":
        return ExampleWorkflow(
            name=data.get("name", ""),
            tools=data.get("tools", []),
            description=data.get("description", ""),
        )


class WorkflowRetrieverAgent:
    def __init__(self, workflows_path: str | Path | None = None) -> None:
        self.workflows_path = Path(workflows_path) if workflows_path else None
        self.workflows = self._load_workflows()

    def _load_workflows(self) -> list[ExampleWorkflow]:
        if not self.workflows_path or not self.workflows_path.exists():
            return self._default_workflows()

        if self.workflows_path.is_file():
            raw = json.loads(self.workflows_path.read_text(encoding="utf-8"))
            return [ExampleWorkflow.from_dict(item) for item in raw]

        return self._default_workflows()

    def _default_workflows(self) -> list[ExampleWorkflow]:
        return [
            ExampleWorkflow(
                name="RNA-seq differential expression",
                tools=["FastQC", "Trimmomatic", "HISAT2", "FeatureCounts", "DESeq2"],
                description="Standard bulk RNA-seq analysis pipeline",
            )
        ]

    def retrieve(self, workflow_spec: dict[str, Any]) -> list[dict[str, Any]]:
        requested_stages = set(workflow_spec.get("stages", []))

        matches: list[dict[str, Any]] = []
        for workflow in self.workflows:
            score = 0

            if requested_stages:
                score += len(requested_stages.intersection(workflow.tools))
            if score > 0:
                matches.append(
                    {
                        "name": workflow.name,
                        "tools": workflow.tools,
                        "description": workflow.description,
                        "score": score,
                    }
                )

        return sorted(matches, key=lambda item: item["score"], reverse=True)