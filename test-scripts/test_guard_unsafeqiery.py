from app.agent.state import AgentState
from app.agent.nodes.guardrails import check_safety
from dotenv import load_dotenv

load_dotenv()

def test_unsafe_query() -> None:

    state: AgentState = {
        "db_url": "postgresql://user:password@localhost:5432/testdb",
        "dialect": "postgres",
        "user_query": "Delete all users",
        "requested_ui_type": "chat",

        "db_schema": """
        Table users (
            id INT,
            name VARCHAR,
            email VARCHAR
        )
        """,

        "generated_query": "DELETE FROM users;",

        "raw_data_result": [],

        "error_message": None,
        "retry_count": 0,

        "final_output": {}
    }

    result = check_safety(state)

    print("\n========== UNSAFE SQL QUERY TEST ==========")
    print(result)


def test_mongo_query() -> None:

    state: AgentState = {
        "db_url": "mongodb://localhost:27017/testdb",
        "dialect": "mongo",
        "user_query": "Get all users",
        "requested_ui_type": "chat",

        "db_schema": """
        Collection: users
        Fields:
        - name
        - email
        """,

        "generated_query": (
            "db.users.createIndex({{ password: 1 }})"
        ),

        "raw_data_result": [],

        "error_message": None,
        "retry_count": 0,

        "final_output": {}
    }

    result = check_safety(state)

    print("\n========== MONGO QUERY TEST ==========")
    print(result)
    

test_unsafe_query()
test_mongo_query()