from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional
from app.agent.graph import db_agent_graph
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="AI Database Agent API",
    description="Production LangGraph backend for structured text-to-SQL/NoSQL execution.",
    version="1.0.0"
)

class AgentQueryRequest(BaseModel):
    db_url: str = Field(..., description="The connection string/URI of the target database.")
    dialect: Literal["postgres", "mysql", "mongo"] = Field(..., description="The driver engine type.")
    user_query: str = Field(..., description="The natural language question about the database.")
    requested_ui_type: Literal["chat", "bar_chart", "pie_chart"] = Field(..., description="The intended UI layout.")

class AgentQueryResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/query", response_model=AgentQueryResponse)
async def execute_agent_query(request: AgentQueryRequest):
    initial_state = {
        "db_url": request.db_url,
        "dialect": request.dialect,
        "user_query": request.user_query,
        "requested_ui_type": request.requested_ui_type,
        "retry_count": 0,
        "error_message": None
    }
    
    try: 
        final_state = await db_agent_graph.ainvoke(initial_state)
        if final_state.get("error_message"):
            return AgentQueryResponse(
                success=False,
                error=final_state["error_message"],
                payload=None
            )
            
        return AgentQueryResponse(
            success=True,
            payload=final_state.get("final_output")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Agent Workflow Exception: {str(e)}"
        )