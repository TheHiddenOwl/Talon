from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class CollectorResult:
    data: Any
    status_code: Optional[int] = 200
    duration_ms: Optional[int] = 0
    raw_response: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "data": self.data,
            "status_code": self.status_code,
            "duration_ms": self.duration_ms,
            "raw_response": self.raw_response,
            "error": self.error
        }
