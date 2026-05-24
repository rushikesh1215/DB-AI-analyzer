from pydantic import BaseModel, Field
from typing import List, TypedDict,Literal,Optional,Dict,Any

#===========================
class ChatResponse(BaseModel):
    """"Schema for plain conversational textual answers. """
    messages: str=Field(description="The direct answer explaining the database findings.")

class BarChartData(BaseModel):
   label:str=Field(description="The category name for the X-axis (e.g., product name, year).")
   value: float = Field(description="The numeric value for the Y-axis.")
   
class BarChartResponse(BaseModel):
    """Schema expected by frontend chart libraries when rendering a bar chart."""
    title:str=Field(description="Descriptive title of the bar chart.")
    x_axis_label: str = Field(description="Label for what the horizontal axis displays.")
    y_axis_label: str = Field(description="Label for what the vertical axis measures.")
    data: List[BarChartData] = Field(description="List of key-value records for rendering rows.")

class PieChartData(BaseModel):
    category: str = Field(description="The slice name (e.g., Department, Country).")
    percentage_or_value: float = Field(description="The numeric weight of this slice.")

class PieChartResponse(BaseModel):
    """Schema expected when rendering a pie or donut chart."""
    title: str = Field(description="Descriptive title of the pie chart.")
    data: List[PieChartData] = Field(description="List of categories and corresponding metrics.")    
        
# ==========================================
# LANGGRAPH STATE DEFINITION

class AgentState(TypedDict):
    db_url: str                                                  # Target database connection string
    dialect: Literal["postgres", "mysql", "mongo"]               # Standard database dialect routing key
    user_query: str                                              # The plain-text natural language question
    requested_ui_type: Literal["chat", "bar_chart", "pie_chart"] # UI layout switch

    db_schema: str                                               # Parsed schema context from 'Schema Reader'
    generated_query: str                                         # Raw executable script output (SQL or NoSQL) 
    raw_data_result: List[Dict[str, Any]]                        # Output records fetched by the execution nodes
    
    error_message: Optional[str]                                 # Error context passed backward when loops trip 
    retry_count: int                                             # Safety threshold breaker to stop infinite looping

    final_output: Dict[str, Any]