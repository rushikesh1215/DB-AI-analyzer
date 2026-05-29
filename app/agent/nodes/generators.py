from pydantic import BaseModel, Field
from typing import Optional,Dict,Any
from app.agent.state import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


class GeneratedQueryOutput(BaseModel):
    """The structured output format expected from the LLM query generator."""
    query_string: str = Field(description="The executable SQL statement OR the stringified JSON query object/pipeline array for MongoDB.")
    mongo_collection: Optional[str] = Field(None, description="REQUIRED ONLY FOR MONGO: The specific collection name to target.")
    
def generate_query(state: AgentState)-> Dict[str,Any]:
    """Generates an optimal database query based on the schema and handles error loops."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",temperature=0, max_retries=0)
    structured_llm = llm.with_structured_output(GeneratedQueryOutput)
    schema_example = GeneratedQueryOutput.model_json_schema()
    system_prompt = (
        "You are an expert database administrator. Your task is to write a highly optimized, syntactically correct query "
        "to answer the user's question based strictly on the provided schema metadata.\n\n"
        "### TARGET DATABASE dialect: {dialect} \n\n"
        "### SCHEMA CONTEXT:\n{db_schema}\n\n"
        "### CRITICAL FORMATTING RULES:\n"
        "1. For Postgres/MySQL: Provide the clean executable SQL query string inside `query_string`.\n"
        "2. For MongoDB: Do NOT write shell wrappers like 'db.find()'. Instead, write a pure JSON query filter object "
        "or a JSON array representing an aggregation pipeline inside `query_string`. Also populate `mongo_collection`.\n"
        "3. Ensure queries are strictly READ-ONLY (SELECT or read operations). Do not modify data."
       "Return ONLY valid JSON matching this schema:{schema}" )
    
    feedback_context = ""
    if state.get("error_message"):
        feedback_context = (
            f"\n\nATTENTION: Your previous query generation failed with the following error:\n"
            f"'{state['error_message']}'\n"
            f"Please review your mistake, adjust syntax or table relationships, and re-generate a correct query."
        )
    
    user_prompt = "User Question: {user_query}" + feedback_context
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt)
    ])
    
    chain = prompt_template | structured_llm
       
    try:
        response: GeneratedQueryOutput = chain.invoke({
            "dialect": state["dialect"],
            "db_schema": state["db_schema"],
            "user_query": state["user_query"],
            "schema":schema_example
        })
        
        query_payload = response.query_string
        
        if state["dialect"] == "mongo" and response.mongo_collection:
              query_payload = f"{response.mongo_collection}|||{response.query_string}"
        
        return {
            "generated_query": query_payload,
            "error_message": None  
        }
        
    except Exception as e:
        return {"error_message": f"Query Generation LLM Failure: {str(e)}"}
        