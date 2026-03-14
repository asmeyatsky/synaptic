"""
Cognitive State Entity

Represents the classified mental state of a user based on neural signals.
Immutable domain model following skill2026.md Rule 3.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, UTC
from enum import Enum
from typing import FrozenSet

from ..events import DomainEvent, ClassificationCompletedEvent


class CognitiveStateType(Enum):
    FOCUS = "focus"
    RELAXED = "relaxed"
    STRESSED = "stressed"
    DROWSY = "drowsy"
    ENGAGED = "engaged"
    MEDITATING = "meditating"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CognitiveState:
    id: str
    session_id: str
    user_id: str
    state_type: CognitiveStateType
    confidence: float
    features_used: FrozenSet[str]
    timestamp: datetime
    domain_events: tuple[DomainEvent, ...] = field(default=())

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

    def with_higher_confidence(
        self, new_confidence: float, new_type: CognitiveStateType
    ) -> "CognitiveState":
        if not 0.0 <= new_confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

        return replace(
            self,
            confidence=new_confidence,
            state_type=new_type,
            timestamp=datetime.now(UTC),
            domain_events=self.domain_events
            + (
                ClassificationCompletedEvent(
                    aggregate_id=self.id,
                    occurred_at=datetime.now(UTC),
                    session_id=self.session_id,
                    state_type=new_type.value,
                    confidence=new_confidence,
                ),
            ),
        )

    def is_reliable(self, threshold: float = 0.7) -> bool:
        return self.confidence >= threshold
