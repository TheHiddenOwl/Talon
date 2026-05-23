import json
from typing import Any, Dict, Optional

class JsonParser:
    @staticmethod
    def parse(data: str) -> Optional[Any]:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def validate(data: Any, schema: Dict[str, Any]) -> bool:
        # Simplified validation logic
        # In a real scenario, use jsonschema library
        return True
