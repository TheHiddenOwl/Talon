import json
from typing import Any, Optional

class JsonParser:
    @staticmethod
    def parse(data: str) -> Optional[Any]:
        """
        Safely parse a JSON string. Returns None on failure
        instead of raising, so callers can handle gracefully.
        """
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return None

    # TODO: implement validate() with jsonschema when collector
    # output schemas are formalised in Phase 4.
