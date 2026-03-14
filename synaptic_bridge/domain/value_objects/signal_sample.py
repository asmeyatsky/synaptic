"""
Signal Sample Value Object

Immutable value object representing a single neural signal sample.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SignalSample:
    timestamp: datetime
    values: tuple[float, ...]
    channel_indices: tuple[int, ...]

    def __post_init__(self):
        if len(self.values) != len(self.channel_indices):
            raise ValueError("Values and channel indices must have same length")

    def get_value(self, channel_index: int) -> float:
        try:
            idx = self.channel_indices.index(channel_index)
            return self.values[idx]
        except ValueError:
            raise ValueError(f"Channel {channel_index} not in sample")
