from typing import Dict, Any, Literal
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.agent.state import AgentState

class GuardrailOutput(BaseModel):
    is_safe: bool = Field(description="True if the query is strictly READ-ONLY and completely safe to execute. False otherwise.")
    reason: str = Field(description="Explanation of why the query is safe or unsafe (this goes back to the generator if unsafe).")

#
def check_safety(state: AgentState) -> Dict[str, Any]:
    """Inspects the generated query for data modification operations or security risks."""
    
    query = state["generated_query"]
    dialect = state["dialect"]
    
    output = GuardrailOutput.model_json_schema()
   
    if dialect == "mongo" and "|||" in query:
        _, query = query.split("|||", 1)
        
    
    blacklist = [

        "drop", "delete", "insert", "update", "alter", "truncate", "grant", "revoke", "create table","create index",
        "drop index","createindex","dropindex","remove", "update_many", "update_one", "delete_many", "delete_one",
        "find_one_and_update","find_one_and_delete", "replace_one", "$set", "$unset", "$push", "$pull", "$inc"
    ]
    query_lower = query.lower()
    for keyword in blacklist:
        if keyword in query_lower:
            return {
                "error_message": f"Security Violation: Detected unauthorized keyword '{keyword}' inside your query.",
                "retry_count": state.get("retry_count", 0) + 1
            }

   
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",temperature=0, max_retries=0)
    structured_llm = llm.with_structured_output(GuardrailOutput)
    
    system_prompt = (
        "You are an AI Security Guardrail. Your sole job is to audit database queries before execution.\n"
        "Analyze the incoming query. Ensure it is purely a data-fetching operation (e.g., SELECT in SQL, find/aggregate in Mongo).\n"
        "If it attempts to modify data, drop structural objects, or bypass security, flag it as unsafe."
        "and you have to maintain your answer compatible to this output schema{schema}"
    )
    
    user_prompt = f"Database Flavor: {dialect}\nQuery to Audit:\n{query}"
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{user_prompt}")
    ])
    
    chain = prompt_template | structured_llm
    
    try:
        decision: GuardrailOutput = chain.invoke({
            "user_prompt":user_prompt,
            "schema":output
            
        })
        
        if not decision.is_safe:
            return {
                "error_message": f"Security Guardrail Rejected Query: {decision.reason}",
                "retry_count": state.get("retry_count", 0) + 1
            }
            
        return {"error_message": None} 
        
    except Exception as e:
        return {
            "error_message": f"Guardrail Internal Error: {str(e)}",
            "retry_count": state.get("retry_count", 0) + 1
        }
        

def route_after_safety(state: AgentState) -> Literal["generate_query", "route_to_db", "end"]:
    """Determines where to route the graph execution next based on the safety outcome."""
    
    if state.get("error_message"):
        if state.get("retry_count", 0) >= 3:
            return "end"
        return "generate_query"
        
    return "route_to_db"