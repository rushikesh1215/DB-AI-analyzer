from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState
from app.agent.nodes.readers import extract_schema
from app.agent.nodes.generators import generate_query
from app.agent.nodes.executors import execute_db_query
from app.agent.nodes.guardrails import check_safety,route_after_safety
from app.agent.nodes.formatters import (
    format_chat_response, 
    format_chart_response, 
  
)


def handle_execution_routing(state: AgentState) -> str:
    """Evaluates error boundaries and decides whether to retry, format, or kill the run."""
    error = state.get("error_message")
    retries = state.get("retry_count", 0)

    if error:   
        if retries >= 3:
            return "exit_workflow"
        return "retry_generation"
        
    if state["requested_ui_type"] == "chat":
        return "chat_branch"
    return "chart_branch"


workflow = StateGraph(AgentState)

workflow.add_node("schema_reader", extract_schema)
workflow.add_node("query_generator", generate_query)
workflow.add_node("safty_check",check_safety)
workflow.add_node("query_executor", execute_db_query)
workflow.add_node("chat_formatter", format_chat_response)
workflow.add_node("chart_formatter", format_chart_response)


workflow.add_edge(START, "schema_reader")
workflow.add_edge("schema_reader", "query_generator")
workflow.add_edge("query_generator", "safty_check")

workflow.add_conditional_edges(
    "safty_check",
    route_after_safety,
    {
        "generate_query": "query_generator", 
        "route_to_db":"query_executor",
        "end":END
    
    }
)                               
workflow.add_conditional_edges(
    "query_executor",
    handle_execution_routing,
    {
        "retry_generation": "query_generator", 
        "chat_branch": "chat_formatter",
        "chart_branch": "chart_formatter",
        "exit_workflow": END                   
    }
)


workflow.add_edge("chat_formatter", END)
workflow.add_edge("chart_formatter", END)

db_agent_graph = workflow.compile()
print(db_agent_graph.get_graph().draw_mermaid())