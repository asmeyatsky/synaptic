"""
Correction Entity

Represents a human override captured by the CLE.
Following PRD: Records original intent, inferred context, called tool, corrected tool, correction metadata, and operator identity.

Immutable domain model following skill2026.md Rule 3.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, UTC
from typing import Any

from ...domain.events import DomainEvent


@dataclass(frozen=True)
class Correction:
    correction_id: str
    session_id: str
    agent_id: str
    original_intent: str
    inferred_context: str
    original_tool: str
    corrected_tool: str
    correction_metadata: dict[str, Any]
    operator_identity: str
    confidence_before: float
    confidence_after: float
    captured_at: datetime
    domain_events: tuple[DomainEvent, ...] = field(default=())

    def __post_init__(self):
        if not 0.0 <= self.confidence_before <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence_after <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

    def trust_score(self) -> float:
        improvement = self.confidence_after - self.confidence_before
        return min(1.0, max(0.0, 0.5 + improvement * 0.5))

    def was_improvement(self) -> bool:
        return self.confidence_after > self.confidence_before


@dataclass(frozen=True)
class CorrectionPattern:
    pattern_id: str
    intent_vector: tuple[float, ...]
    original_tools: tuple[str, ...]
    corrected_tools: tuple[str, ...]
    occurrence_count: int
    avg_confidence_improvement: float
    last_updated: datetime

    def with_increment(self, confidence_improvement: float) -> "CorrectionPattern":
        new_count = self.occurrence_count + 1
        new_avg = (
            self.avg_confidence_improvement * self.occurrence_count
            + confidence_improvement
        ) / new_count
        return replace(
            self,
            occurrence_count=new_count,
            avg_confidence_improvement=new_avg,
            last_updated=datetime.now(UTC),
        )

    def matches_intent(self, intent_vector: tuple[float, ...]) -> float:
        if len(intent_vector) != len(self.intent_vector):
            return 0.0

        dot_product = sum(a * b for a, b in zip(intent_vector, self.intent_vector))
        mag_a = sum(a * a for a in intent_vector) ** 0.5
        mag_b = sum(b * b for b in self.intent_vector) ** 0.5

        if mag_a == 0 or mag_b == 0:
            return 0.0

        return dot_product / (mag_a * mag_b)
