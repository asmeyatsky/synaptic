"""
Session Entity

Represents a recording/control session between user and BCI system.
Immutable domain model following skill2026.md Rule 3.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, UTC
from enum import Enum
from typing import FrozenSet

from ..events import DomainEvent, SessionStartedEvent, SessionEndedEvent


class SessionStatus(Enum):
    INITIATED = "initiated"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass(frozen=True)
class Session:
    id: str
    user_id: str
    status: SessionStatus
    started_at: datetime
    ended_at: datetime | None
    device_ids: FrozenSet[str]
    signal_count: int
    classification_count: int
    domain_events: tuple[DomainEvent, ...] = field(default=())

    def start(self) -> "Session":
        return replace(
            self,
            status=SessionStatus.ACTIVE,
            domain_events=self.domain_events
            + (
                SessionStartedEvent(
                    aggregate_id=self.id,
                    occurred_at=datetime.now(UTC),
                    user_id=self.user_id,
                ),
            ),
        )

    def pause(self) -> "Session":
        return replace(
            self,
            status=SessionStatus.PAUSED,
        )

    def resume(self) -> "Session":
        return replace(
            self,
            status=SessionStatus.ACTIVE,
        )

    def complete(self) -> "Session":
        return replace(
            self,
            status=SessionStatus.COMPLETED,
            ended_at=datetime.now(UTC),
            domain_events=self.domain_events
            + (
                SessionEndedEvent(
                    aggregate_id=self.id,
                    occurred_at=datetime.now(UTC),
                    user_id=self.user_id,
                    duration_seconds=(
                        datetime.now(UTC) - self.started_at
                    ).total_seconds(),
                ),
            ),
        )

    def add_signal(self) -> "Session":
        return replace(
            self,
            signal_count=self.signal_count + 1,
        )

    def add_classification(self) -> "Session":
        return replace(
            self,
            classification_count=self.classification_count + 1,
        )

    def is_active(self) -> bool:
        return self.status == SessionStatus.ACTIVE
