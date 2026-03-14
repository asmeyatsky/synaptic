"""
Domain Events Base

Base class and utilities for domain events.
Following skill2026.md event-driven communication patterns.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    aggregate_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_type(self) -> str:
        return self.__class__.__name__


@dataclass(frozen=True)
class SignalAcquiredEvent(DomainEvent):
    session_id: str = ""
    channel_count: int = 0
    note: str = ""


@dataclass(frozen=True)
class ClassificationCompletedEvent(DomainEvent):
    session_id: str = ""
    state_type: str = ""
    confidence: float = 0.0


@dataclass(frozen=True)
class DeviceCommandExecutedEvent(DomainEvent):
    command: str = ""
    parameters: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SessionStartedEvent(DomainEvent):
    user_id: str = ""


@dataclass(frozen=True)
class SessionEndedEvent(DomainEvent):
    user_id: str = ""
    duration_seconds: float = 0.0


@dataclass(frozen=True)
class UserRegisteredEvent(DomainEvent):
    email: str = ""
    name: str = ""


@dataclass(frozen=True)
class DeviceConnectedEvent(DomainEvent):
    device_name: str = ""
    device_type: str = ""
