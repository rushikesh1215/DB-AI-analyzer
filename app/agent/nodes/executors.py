import json
from typing import Dict, Any, List
from sqlalchemy import create_engine, text
from pymongo import MongoClient
from app.agent.state import AgentState


def _execute_sql(db_url: str, sql_query: str) -> List[Dict[str, Any]]:
    """Executes a plain text SQL query and marshals rows to standard dict arrays."""
    engine = create_engine(db_url)
    with engine.connect() as connection:
        result = connection.execute(text(sql_query))
 
        if result.returns_rows:
            return [dict(row._mapping) for row in result]
        return [{"message": f"Query executed successfully. Affected rows: {result.rowcount}"}]


def _execute_mongo(db_url: str, packed_query: str) -> List[Dict[str, Any]]:
    """Decodes the custom string payload and runs the query or aggregation pipeline."""

    if "|||" not in packed_query:
        raise ValueError("Invalid MongoDB execution format. Missing collection context separator '|||'.")
        
    collection_name, raw_json = packed_query.split("|||", 1)
    query_data = json.loads(raw_json)
    
    client = MongoClient(db_url)
    db = client.get_default_database()
    collection = db[collection_name]
    
    records = []

    if isinstance(query_data, list):
        cursor = collection.aggregate(query_data)
    else:
        cursor = collection.find(query_data)
        
    for doc in cursor:
        
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        records.append(doc)
        
    client.close()
    return records

def execute_db_query(state: AgentState) -> Dict[str, Any]:
    """Routes query execution dynamically to its corresponding database engine driver."""
    flavor = state["db_flavor"]
    url = state["db_url"]
    query = state["generated_query"]
    
    if not query:
        return {"error_message": "Execution halted: No executable query was passed to this node."}
        
    try:
        if flavor in ["postgres", "mysql"]:
            data_out = _execute_sql(url, query)
        elif flavor == "mongo":
            data_out = _execute_mongo(url, query)
        else:
            raise ValueError(f"Unknown driver engine: {flavor}")
            
        return {
            "raw_data_result": data_out,
            "error_message": None  
        }
    except Exception as e:
       return {"error_message": f"Database Runtime Error: {str(e)}"}