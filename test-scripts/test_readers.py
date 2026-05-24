from app.agent.nodes.readers import extract_schema


mock_state = {
    "db_url": "mongodb://localhost:27017/user", 
    "dialect": "mongo",
    "user_query": "Show me total products",
    "requested_ui_type": "chat",
    "db_schema": "",
    "generated_query": "",
    "raw_data_result": [],
    "error_message": None,
    "retry_count": 0,
    "final_output": {}
}


print("Testing extract_schema node...")
result = extract_schema(mock_state)


print("\n--- TEST RESULT STATE DELTA ---")
print(result)