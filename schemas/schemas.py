from __future__ import annotations
from dataclasses import dataclass
from typing import Annotated, TypedDict


@dataclass
class WorkflowSpec:
    goal: str
    stages: list[str]


class WorkflowState(TypedDict, total=False):
    user_request: str
    workflow_spec: dict
    candidate_tools: list[dict]
    workflow_examples: list[dict]
    workflow_graph: dict
    validation_report: dict
    final_workflow: dict