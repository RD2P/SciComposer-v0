from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


CheckStatus = Literal["PASS", "FAIL", "UNKNOWN"]


@dataclass
class ValidationError:
    type: str
    message: str
    tool_id: str | None = None
    node_id: str | None = None
    edge_index: int | None = None
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type,
            "message": self.message,
        }
        if self.tool_id is not None:
            payload["tool_id"] = self.tool_id
        if self.node_id is not None:
            payload["node_id"] = self.node_id
        if self.edge_index is not None:
            payload["edge_index"] = self.edge_index
        if self.details is not None:
            payload["details"] = self.details
        return payload


@dataclass
class ValidationReport:
    valid: bool
    errors: list[ValidationError]
    checks: dict[str, CheckStatus]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": [error.to_dict() for error in self.errors],
            "checks": self.checks,
        }
