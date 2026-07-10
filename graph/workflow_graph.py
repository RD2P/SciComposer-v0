from langgraph.graph import START, END, StateGraph
from schemas.schemas import WorkflowState
from agents.planner import PlannerAgent

planner_agent = PlannerAgent()

def planner_node(state: WorkflowState) -> WorkflowState:
    request = state.get("user_request", "") or ""
    res = planner_agent.plan(request)
    # print(res)
    
    return {
        "workflow_spec": res
    }


def tool_retriever_node(state: WorkflowState) -> WorkflowState:
    return {
        "candidate_tools": [
            # {"stage": "input_qc", "tool": "FastQC"},
            # {"stage": "preprocessing", "tool": "Trimmomatic"},
            # {"stage": "analysis", "tool": "DESeq2"},
            # {"stage": "reporting", "tool": "Volcano Plot"},
        ]
    }


def workflow_retriever_node(state: WorkflowState) -> WorkflowState:
    return {
        "workflow_examples": [
            {
                # "name": "RNA-seq differential expression",
                # "tools": ["FastQC", "Trimmomatic", "DESeq2"],
            }
        ]
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
    graph.add_node("tool_retriever", tool_retriever_node)
    graph.add_node("workflow_retriever", workflow_retriever_node)
    graph.add_node("builder", builder_node)
    graph.add_node("validator", validator_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "tool_retriever")
    graph.add_edge("tool_retriever", "workflow_retriever")
    graph.add_edge("workflow_retriever", "builder")
    graph.add_edge("builder", "validator")
    graph.add_edge("validator", END)

    return graph.compile()