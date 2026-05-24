from typing import Dict, Any
from sqlalchemy import create_engine, inspect
from pymongo import MongoClient
from app.agent.state import AgentState


def _extract_sql_schema(db_url: str) -> str:
    """Uses SQLAlchemy Reflection to extract explicit structural constraints."""
    engine = create_engine(db_url)
    inspector = inspect(engine)
    schema_parts = []

    for table_name in inspector.get_table_names():
        schema_parts.append(f"Table: {table_name}")
        
        columns = inspector.get_columns(table_name)
        pk_cols = inspector.get_pk_constraint(table_name).get("constrained_columns", [])
        
        schema_parts.append("  Columns:")
        for col in columns:
            col_name = col["name"]
            col_type = str(col["type"])
            is_pk = " [PRIMARY KEY]" if col_name in pk_cols else ""
            nullable = " NULL" if col.get("nullable", True) else " NOT NULL"
            schema_parts.append(f"    - {col_name} ({col_type}){is_pk}{nullable}")
            
        fks = inspector.get_foreign_keys(table_name)
        if fks:
            schema_parts.append("  Foreign Keys / Relationships:")
            for fk in fks:
                constrained = fk["constrained_columns"]
                referred_table = fk["referred_table"]
                referred_cols = fk["referred_columns"]
                schema_parts.append(f"    - {constrained} -> {referred_table}({referred_cols})")
                
        indexes = inspector.get_indexes(table_name)
        if indexes:
            schema_parts.append("  Indexes:")
            for idx in indexes:
                indexed_cols = idx.get("column_names", [])
                included_cols = idx.get("include_columns", [])

                schema_parts.append(f"    - {idx['name']} "
                                    f"(Indexed: {indexed_cols}, Included: {included_cols})"
                                    )  
        schema_parts.append("-" * 10)
        
    engine.dispose()
    return "\n".join(schema_parts)


def _extract_mongo_schema(db_url: str) -> str:
    """Inspects MongoDB system catalogs for structural schemas and index keys."""
    client = MongoClient(db_url)
    db = client.get_default_database()
    schema_parts = []
    
    
    collections_metadata = db.list_collections()
    
    for coll_meta in collections_metadata:
        coll_name = coll_meta["name"]
        schema_parts.append(f"Collection: {coll_name}")
        
       
        options = coll_meta.get("options", {})
        validator = options.get("validator", {})
        json_schema = validator.get("$jsonSchema", {})
        
        if json_schema:
            schema_parts.append("  Schema Validator Rules:")
            required_fields = json_schema.get("required", [])
            properties = json_schema.get("properties", {})
            
            for prop_name, prop_meta in properties.items():
                b_type = prop_meta.get("bsonType", "unknown")
                req = " [REQUIRED]" if prop_name in required_fields else ""
                schema_parts.append(f"    - {prop_name} (Type: {b_type}){req}")
        else:
            
            sample_doc = db[coll_name].find_one()
            if sample_doc:
                schema_parts.append("  Inferred Fields (From Sample Record):")
                for field, value in sample_doc.items():
                    schema_parts.append(f"    - {field} (Type: {type(value).__name__})")
            else:
                schema_parts.append("  Schema Info: Collection empty with no configured schema validators.")
                
        
        try:
            indexes = list(db[coll_name].list_indexes())
            if indexes:
                schema_parts.append("  Indexes:")
                for idx in indexes:
                    schema_parts.append(f"    - {idx['name']} (Key Spec: {idx['key'].to_dict()})")
        except Exception:
            pass
            
        schema_parts.append("-" * 10)
        
    client.close()
    return "\n".join(schema_parts)


def extract_schema(state: AgentState) -> Dict[str, Any]:
    dialect = state["dialect"]
    url = state["db_url"]
    
    try:
        if dialect in ["postgres", "mysql"]:
            schema_text = _extract_sql_schema(url)
        elif dialect == "mongo":
            schema_text = _extract_mongo_schema(url)
        else:
            raise ValueError(f"Unsupported flavor type: {dialect}")
            
        return {"db_schema": schema_text, "error_message": None}
    except Exception as e:
        return {"error_message": f"Metadata extraction failed: {str(e)}"}