from langgraph.graph import StateGraph, END
from src.agents.state import ResearchState
from src.agents.nodes.router import route_query_node
from src.agents.nodes.planner import plan_research_node
from src.agents.nodes.researcher import execute_step_node
from src.agents.nodes.reporter import generate_report_node


def await_approval_node(state: dict) -> dict:
    return state


def should_continue(state: dict) -> str:
    if state.get("error"):
        return END
    if state.get("all_complete"):
        return "generate_report"
    return "execute_step"


def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("route_query", route_query_node)
    graph.add_node("plan_research", plan_research_node)
    graph.add_node("await_approval", await_approval_node)
    graph.add_node("execute_step", execute_step_node)
    graph.add_node("generate_report", generate_report_node)

    graph.set_entry_point("route_query")
    graph.add_edge("route_query", "plan_research")
    graph.add_edge("plan_research", "await_approval")
    graph.add_conditional_edges(
        "await_approval",
        lambda s: "execute_step" if s["plan_approved"] else END
    )
    graph.add_conditional_edges("execute_step", should_continue)
    graph.add_edge("generate_report", END)

    return graph.compile()


research_graph = build_graph()