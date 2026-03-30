"""
Execution Session Entity

Represents a short-lived agent session with execution token.
Following PRD: Each agent session receives a short-lived execution token
(JWT, 15-minute default TTL).

Immutable domain model following skill2026.md Rule 3.
"""

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import Enum

from ...domain.events import DomainEvent


class SessionStatus(Enum):
    INITIATED = "initiated"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


@dataclass(frozen=True)
class ExecutionSession:
    session_id: str
    agent_id: str
    execution_token: str
    status: SessionStatus
    started_at: datetime
    expires_at: datetime
    tool_calls: tuple[str, ...]
    created_by: str
    domain_events: tuple[DomainEvent, ...] = field(default=())

    def __post_init__(self):
        if isinstance(self.expires_at, (int, float)):
            pass
        elif self.expires_at <= self.started_at:
            raise ValueError("Expiration must be after start")

    def is_expired(self) -> bool:
        if isinstance(self.expires_at, (int, float)):
            exp_time = datetime.fromtimestamp(self.expires_at, UTC)
        else:
            exp_time = self.expires_at
        return datetime.now(UTC) >= exp_time

    def is_active(self) -> bool:
        return self.status == SessionStatus.ACTIVE and not self.is_expired()

    def add_tool_call(self, tool_call_id: str) -> "ExecutionSession":
        return replace(
            self,
            tool_calls=self.tool_calls + (tool_call_id,),
        )

    def terminate(self) -> "ExecutionSession":
        return replace(
            self,
            status=SessionStatus.TERMINATED,
            domain_events=self.domain_events
            + (
                SessionEndedEvent(
                    aggregate_id=self.session_id,
                    occurred_at=datetime.now(UTC),
                    agent_id=self.agent_id,
                    reason="terminated_by_user",
                ),
            ),
        )

    def expire(self) -> "ExecutionSession":
        return replace(
            self,
            status=SessionStatus.EXPIRED,
            domain_events=self.domain_events
            + (
                SessionEndedEvent(
                    aggregate_id=self.session_id,
                    occurred_at=datetime.now(UTC),
                    agent_id=self.agent_id,
                    reason="token_expired",
                ),
            ),
        )


from ...domain.events import SessionEndedEvent
