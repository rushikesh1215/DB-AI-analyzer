from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.agent.state import AgentState


def format_chat_response(state: AgentState) -> Dict[str, Any]:
    """Uses LLM to summarize raw data results into a conversational response."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",temperature=0, max_retries=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful data analyst assistant. Answer the user's question accurately using exclusively the provided query results. Keep your response concise and professional."),
        ("human", "User Question: {user_query}\n\nExecuted Query: {generated_query}\n\nQuery Results:\n{raw_data}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "user_query": state["user_query"],
        "generated_query": state["generated_query"],
        "raw_data": str(state["raw_data_result"][:50]) 
    })
    
    return {"final_output": {"type": "chat", "content": response.content}}


def format_chart_response(state: AgentState) -> Dict[str, Any]:
    """Bypasses LLM entirely. Instantly maps raw data rows into Frontend-ready chart JSON."""
    raw_data = state["raw_data_result"]
    ui_type = state["requested_ui_type"]
    
    if not raw_data:
        return {"final_output": {"type": ui_type, "data": [], "error": "No data returned from query."}}
        
    
    keys = list(raw_data[0].keys())
    label_key = keys[0]
    value_key = keys[1] if len(keys) > 1 else keys[0]
    
    formatted_data = []
    for row in raw_data:
        formatted_data.append({
            "label": str(row.get(label_key)),
            "value": float(row.get(value_key)) if isinstance(row.get(value_key), (int, float)) else row.get(value_key)
        })
        
    return {
        "final_output": {
            "type": ui_type,
            "title": f"Data representation for: {state['user_query']}",
            "data": formatted_data
        }
    }


