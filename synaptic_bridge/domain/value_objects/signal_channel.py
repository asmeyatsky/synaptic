"""
Signal Channel Value Object

Immutable value object representing a neural signal channel.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SignalChannel:
    name: str
    index: int
    label: str
    unit: str = "uV"

    def __post_init__(self):
        if self.index < 0:
            raise ValueError("Channel index must be non-negative")
