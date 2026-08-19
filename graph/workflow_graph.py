from langgraph.graph import START, END, StateGraph
from schemas.schemas import WorkflowState
from agents.planner import PlannerAgent
from agents.retriever import RetrieverAgent

planner_agent = PlannerAgent()
retriever_agent: RetrieverAgent | None = None

def planner_node(state: WorkflowState) -> WorkflowState:
    request = state.get("user_request", "") or ""
    res = planner_agent.plan(request)
    
    return {
        "workflow_plan": res
    }


def retriever_node(state: WorkflowState) -> WorkflowState:
    global retriever_agent
    if retriever_agent is None:
        retriever_agent = RetrieverAgent()

    plan = state.get("workflow_plan", {})
    goal = plan.get("goal", "")
    stages = plan.get("stages", [])
    candidate_tools: list[dict] = []
    stage_context = []
    for stage in stages:
        stage_name = stage.get("name", "")
        description = stage.get("description", "")
        stage_context.append(f"{stage_name}: {description}")
        for tool in retriever_agent.retrieve_tools(
            f"{goal}. {stage_name}: {description}", top_k=3
        ):
            candidate_tools.append(
                {**tool, "stage": stage_name, "tool": tool.get("name", "")}
            )

    workflow_query = ". ".join([goal, *stage_context]).strip()
    return {
        "candidate_tools": candidate_tools,
        "workflow_examples": retriever_agent.retrieve_workflows(workflow_query),
    }


def builder_node(state: WorkflowState) -> WorkflowState:
    tools = state.get("candidate_tools", [])
    return {
        "workflow_graph": {
            # "nodes": tools,
            # "edges": [
            #     ("FastQC", "Trimmomatic"),
            #     ("Trimmomatic", "DESeq2"),
            # ],
        }
    }


def validator_node(state: WorkflowState) -> WorkflowState:
    graph = state.get("workflow_graph", {})
    return {
        # "validation_report": {
        #     "valid": bool(graph),
        #     "issues": [],
        # },
        # "final_workflow": graph,
    }


def build_workflow_graph():
    graph = StateGraph(WorkflowState)

    graph.add_node("planner", planner_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("builder", builder_node)
    graph.add_node("validator", validator_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "retriever")
    graph.add_edge("retriever", "builder")
    graph.add_edge("builder", "validator")
    graph.add_edge("validator", END)

    return graph.compile()