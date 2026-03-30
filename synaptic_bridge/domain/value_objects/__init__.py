"""
Value Objects

Immutable value objects for domain concepts.
Following skill2026.md Rule 3.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutionToken:
    token: str
    session_id: str
    issued_at: Any
    expires_at: Any

    def is_expired(self) -> bool:
        from datetime import UTC, datetime

        return datetime.now(UTC) >= self.expires_at


@dataclass(frozen=True)
class ToolResult:
    success: bool
    data: Any
    error: str | None
    execution_time_ms: float

    @property
    def is_error(self) -> bool:
        return not self.success


@dataclass(frozen=True)
class CorrectionScore:
    confidence_before: float
    confidence_after: float
    trust_score: float

    @property
    def improvement(self) -> float:
        return self.confidence_after - self.confidence_before

    @property
    def is_improvement(self) -> bool:
        return self.improvement > 0


@dataclass(frozen=True)
class IntentEmbedding:
    text: str
    vector: tuple[float, ...]

    def cosine_similarity(self, other: "IntentEmbedding") -> float:
        if len(self.vector) != len(other.vector):
            return 0.0

        dot = sum(a * b for a, b in zip(self.vector, other.vector))
        mag_self = sum(a * a for a in self.vector) ** 0.5
        mag_other = sum(b * b for b in other.vector) ** 0.5

        if mag_self == 0 or mag_other == 0:
            return 0.0

        return dot / (mag_self * mag_other)


@dataclass(frozen=True)
class PolicyRule:
    policy_id: str
    name: str
    rego_code: str
    effect: str

    def __post_init__(self):
        if self.effect not in ("allow", "deny"):
            raise ValueError("Effect must be 'allow' or 'deny'")
