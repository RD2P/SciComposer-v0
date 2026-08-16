from typing import TypedDict


class WorkflowStage(TypedDict):
    name: str
    description: str


class WorkflowPlan(TypedDict):
    goal: str
    stages: list[WorkflowStage]


class WorkflowState(TypedDict, total=False):
    user_request: str

    # Planner output
    workflow_plan: WorkflowPlan

    # Retriever output
    candidate_tools: list[dict]
    workflow_examples: list[dict]

    # Builder output
    workflow_graph: dict

    # Validator output
    validation_report: dict

    # Final output
    final_workflow: dict