"""
Classification Result Value Object

Immutable value object representing cognitive state classification output.
"""

from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class ClassificationResult:
    state_type: str
    confidence: float
    features_used: FrozenSet[str]
    alternative_states: FrozenSet[str]

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

    def is_reliable(self, threshold: float = 0.7) -> bool:
        return self.confidence >= threshold
