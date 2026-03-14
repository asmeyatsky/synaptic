"""
User Entity

Represents a user of the SynapticBridge BCI system.
Immutable domain model following skill2026.md Rule 3.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, UTC
from typing import FrozenSet

from ..events import DomainEvent
from ..value_objects import UserPreferences


@dataclass(frozen=True)
class User:
    id: str
    email: str
    name: str
    preferences: UserPreferences
    registered_at: datetime
    last_active_at: datetime
    domain_events: tuple[DomainEvent, ...] = field(default=())

    def update_preferences(self, new_preferences: UserPreferences) -> "User":
        return replace(
            self,
            preferences=new_preferences,
            last_active_at=datetime.now(UTC),
        )

    def mark_active(self) -> "User":
        return replace(
            self,
            last_active_at=datetime.now(UTC),
        )

    def is_active(self) -> bool:
        now = datetime.now(UTC)
        inactive_duration = now - self.last_active_at
        return inactive_duration.total_seconds() < 86400
