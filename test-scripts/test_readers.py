from app.agent.nodes.readers import extract_schema
from app.agent.nodes.generators import generate_query
from dotenv import load_dotenv

load_dotenv()

mock_state = {
    "db_url": "mongodb://localhost:27017/user",
    "dialect": "mongo",
    "user_query": "How many users are their",
    "requested_ui_type": "chat",

    "db_schema": "",
    "generated_query": "",
    "raw_data_result": [],
    "error_message": None,
    "retry_count": 0,
    "final_output": {}
}

print("Testing extract_schema node...\n")

schema_result = extract_schema(mock_state)

print("\n--- EXTRACT_SCHEMA RESULT ---")
print(schema_result)

mock_state.update(schema_result)

print("\n\nTesting generate_query node...\n")

query_result = generate_query(mock_state)

print("\n--- GENERATE_QUERY RESULT ---")
print(query_result)

mock_state.update(query_result)

print("\n--- FINAL STATE ---")
print(mock_state)
