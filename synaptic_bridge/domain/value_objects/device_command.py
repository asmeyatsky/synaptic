"""
Device Command Value Object

Immutable value object representing a command to be executed on a device.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DeviceCommand:
    command_type: str
    parameters: tuple[tuple[str, float], ...]
    issued_at: datetime
    issued_by: str

    def get_parameter(self, key: str) -> float:
        for k, v in self.parameters:
            if k == key:
                return v
        raise ValueError(f"Parameter {key} not found")

    def has_parameter(self, key: str) -> bool:
        return any(k == key for k, _ in self.parameters)
