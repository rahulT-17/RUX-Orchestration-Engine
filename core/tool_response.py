# tool_response.py : ToolResponse is the standard result object every tool returns so 
# the runtime always receives one predictable shape instead of mixed strings and dicts.

from enum import Enum
from dataclasses import dataclass

class ToolStatus(str,Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"

@dataclass

class ToolResponse:
    status: ToolStatus
    message: str
    data: dict | None = None
    error: str | None = None
    metadata: dict | None = None
    latency_ms: float | None = None

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "message": self.message,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "latency_ms": self.latency_ms,
        }