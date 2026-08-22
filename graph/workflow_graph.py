from langgraph.graph import START, END, StateGraph
from ollama import Client
from schemas.schemas import WorkflowState
from agents.planner import PlannerAgent
from agents.retriever import RetrieverAgent
from agents.builder import BuilderAgent
from validator.validator import DeterministicWorkflowValidator

OLLAMA_MODEL = "qwen3.5:9b"
ollama_client = Client()
planner_agent = PlannerAgent(model=OLLAMA_MODEL, client=ollama_client)
builder_agent = BuilderAgent(model=OLLAMA_MODEL, client=ollama_client)
retriever_agent: RetrieverAgent | None = None
validator = DeterministicWorkflowValidator()

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
    stage_context = []
    for stage in stages:
        stage_name = stage.get("name", "")
        description = stage.get("description", "")
        stage_context.append(f"{stage_name}: {description}")

    workflow_query = ". ".join([goal, *stage_context]).strip()
    return {
        "candidate_tools": retriever_agent.retrieve_plan_tools(plan, top_k=3),
        "workflow_examples": retriever_agent.retrieve_workflows(workflow_query),
    }


def builder_node(state: WorkflowState) -> dict:
    result = builder_agent.build(
        user_request=state["user_request"],
        workflow_plan=state["workflow_plan"],
        candidate_tools=state["candidate_tools"],
        workflow_examples=state["workflow_examples"],
    )

    return {
        "workflow_graph": result
    }


def validator_node(state: WorkflowState) -> WorkflowState:
    graph = state.get("workflow_graph", {})
    
    # Validate the workflow graph
    validation_result = validator.validate(graph)
    
    return {
        "validation_report": validation_result,
        "final_workflow": graph,
        "is_valid": validation_result.get("valid", False)
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