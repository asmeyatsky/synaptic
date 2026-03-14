"""
Tool Call Entity

Represents a tool invocation within an execution session.
Following PRD: Audit logging of all tool calls.

Immutable domain model following skill2026.md Rule 3.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, UTC
from typing import Any
from enum import Enum

from ...domain.events import DomainEvent


class ToolCallStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CORRECTED = "corrected"


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    session_id: str
    agent_id: str
    tool_name: str
    corrected_tool: str | None
    parameters: dict[str, Any]
    status: ToolCallStatus
    started_at: datetime
    completed_at: datetime | None
    result: Any
    error: str | None
    was_corrected: bool
    correction_confidence: float | None
    domain_events: tuple[DomainEvent, ...] = field(default=())

    def mark_in_progress(self) -> "ToolCall":
        return replace(
            self,
            status=ToolCallStatus.IN_PROGRESS,
        )

    def complete_success(self, result: Any) -> "ToolCall":
        return replace(
            self,
            status=ToolCallStatus.SUCCESS,
            completed_at=datetime.now(UTC),
            result=result,
        )

    def complete_failure(self, error: str) -> "ToolCall":
        return replace(
            self,
            status=ToolCallStatus.FAILED,
            completed_at=datetime.now(UTC),
            error=error,
        )

    def apply_correction(self, corrected_tool: str, confidence: float) -> "ToolCall":
        return replace(
            self,
            corrected_tool=corrected_tool,
            status=ToolCallStatus.CORRECTED,
            was_corrected=True,
            correction_confidence=confidence,
            domain_events=self.domain_events
            + (
                ToolCalledEvent(
                    aggregate_id=self.call_id,
                    occurred_at=datetime.now(UTC),
                    session_id=self.session_id,
                    agent_id=self.agent_id,
                    tool_name=corrected_tool,
                    was_corrected=True,
                ),
            ),
        )

    def to_audit_dict(self) -> dict:
        return {
            "call_id": self.call_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "tool_name": self.tool_name,
            "corrected_tool": self.corrected_tool,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "was_corrected": self.was_corrected,
            "error": self.error,
        }


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: str
    session_id: str | None
    agent_id: str | None
    tool_name: str | None
    action: str
    actor: str
    resource: str
    outcome: str
    metadata: dict[str, Any]
    timestamp: datetime
    signature: str

    def is_critical(self) -> bool:
        return self.event_type in (
            "policy_violation",
            "credential_access",
            "network_call",
        )

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "tool_name": self.tool_name,
            "action": self.action,
            "actor": self.actor,
            "resource": self.resource,
            "outcome": self.outcome,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "signature": self.signature,
        }
