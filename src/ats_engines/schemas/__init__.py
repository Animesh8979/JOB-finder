import json
from pathlib import Path
from typing import Dict, Any

_schemas_cache: Dict[str, Dict[str, Any]] = {}

def load_schema(engine_name: str) -> Dict[str, Any]:
    if engine_name in _schemas_cache:
        return _schemas_cache[engine_name]
    
    schema_path = Path(__file__).parent / f"{engine_name}.json"
    if not schema_path.exists():
        # Fallback to empty schema which allows nothing by default
        return {"engine": engine_name, "allowed_fields": [], "allowed_actions": [], "blocked_actions": ["*"]}
        
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
        _schemas_cache[engine_name] = schema
        return schema

def is_action_allowed(engine_name: str, action: str) -> bool:
    schema = load_schema(engine_name)
    
    blocked = schema.get("blocked_actions", [])
    if "*" in blocked or action in blocked:
        return False
        
    allowed = schema.get("allowed_actions", [])
    return action in allowed

def is_field_allowed(engine_name: str, field_name: str) -> bool:
    schema = load_schema(engine_name)
    allowed = schema.get("allowed_fields", [])
    return field_name in allowed
