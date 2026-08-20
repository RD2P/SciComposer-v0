from typing import TypedDict


class WorkflowStage(TypedDict):
    name: str
    description: str


class WorkflowPlan(TypedDict):
    goal: str
    stages: list[WorkflowStage]


class ToolCandidateGroup(TypedDict):
    stage: str
    description: str
    candidates: list[dict]


class WorkflowState(TypedDict, total=False):
    user_request: str

    # Planner output
    workflow_plan: WorkflowPlan

    # Retriever output
    candidate_tools: list[ToolCandidateGroup]
    workflow_examples: list[dict]

    # Builder output
    workflow_graph: dict

    # Validator output
    validation_report: dict

    # Final output
    final_workflow: dict