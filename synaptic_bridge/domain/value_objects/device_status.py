"""
Device Status Value Object

Immutable value object representing the current status of a device.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class DeviceStatus:
    device_id: str
    is_connected: bool
    last_update: datetime
    state: str
    metrics: tuple[tuple[str, Any], ...]

    def get_metric(self, key: str) -> Any:
        for k, v in self.metrics:
            if k == key:
                return v
        return None

    def is_operational(self) -> bool:
        return self.is_connected and self.state == "operational"
