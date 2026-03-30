"""
Correction Entity

Represents a human override captured by the CLE.
Following PRD: Records original intent, inferred context, called tool, corrected tool, correction metadata, and operator identity.

Immutable domain model following skill2026.md Rule 3.
"""

import math
from dataclasses import dataclass, field, replace
from datetime import datetime, UTC
from typing import Any

from ...domain.events import DomainEvent


PATTERN_DECAY_HALF_LIFE_DAYS = 30.0


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
    total_undo_count: int = 0

    def with_increment(self, confidence_improvement: float) -> "CorrectionPattern":
        new_count = self.occurrence_count + 1
        new_avg = (
            self.avg_confidence_improvement * self.occurrence_count + confidence_improvement
        ) / new_count
        return replace(
            self,
            occurrence_count=new_count,
            avg_confidence_improvement=new_avg,
            last_updated=datetime.now(UTC),
        )

    def with_undo(self) -> "CorrectionPattern":
        """Mark that a correction based on this pattern was undone."""
        return replace(
            self,
            total_undo_count=self.total_undo_count + 1,
            last_updated=datetime.now(UTC),
        )

    def _calculate_decay_factor(self, now: datetime | None = None) -> float:
        """Calculate decay factor based on pattern age.

        Uses exponential decay with configurable half-life.
        Returns a value between 0.0 and 1.0.
        """
        if now is None:
            now = datetime.now(UTC)

        age_seconds = (now - self.last_updated).total_seconds()
        age_days = age_seconds / (24 * 60 * 60)

        decay_factor = math.exp(-0.69314718 * age_days / PATTERN_DECAY_HALF_LIFE_DAYS)
        return max(0.0, min(1.0, decay_factor))

    def _calculate_undo_penalty(self) -> float:
        """Calculate penalty factor based on undo rate.

        If corrections based on this pattern are frequently undone,
        the pattern confidence should decrease.
        """
        if self.occurrence_count == 0:
            return 1.0

        undo_rate = self.total_undo_count / self.occurrence_count
        return max(0.0, 1.0 - undo_rate)

    def matches_intent(self, intent_vector: tuple[float, ...]) -> float:
        """Calculate similarity with decay applied."""
        if len(intent_vector) != len(self.intent_vector):
            return 0.0

        dot_product = sum(a * b for a, b in zip(intent_vector, self.intent_vector))
        mag_a = sum(a * a for a in intent_vector) ** 0.5
        mag_b = sum(b * b for b in self.intent_vector) ** 0.5

        if mag_a == 0 or mag_b == 0:
            return 0.0

        raw_similarity = dot_product / (mag_a * mag_b)

        decay_factor = self._calculate_decay_factor()
        undo_penalty = self._calculate_undo_penalty()

        return raw_similarity * decay_factor * undo_penalty

    def effective_confidence(self, intent_vector: tuple[float, ...]) -> float:
        """Get the effective confidence for this pattern matching an intent."""
        base_similarity = self.matches_intent(intent_vector)

        occurrence_boost = min(1.0, self.occurrence_count / 10.0)
        avg_improvement_boost = max(0.0, self.avg_confidence_improvement)

        effective = base_similarity * (0.7 + 0.2 * occurrence_boost + 0.1 * avg_improvement_boost)

        return min(1.0, max(0.0, effective))
