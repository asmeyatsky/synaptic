"""
Device Entity

Represents an external controllable device linked to the BCI system.
Immutable domain model following skill2026.md Rule 3.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, UTC
from enum import Enum

from ..events import DomainEvent, DeviceCommandExecutedEvent


class DeviceType(Enum):
    PROSTHETIC = "prosthetic"
    ROBOTIC_ARM = "robotic_arm"
    EXOSKELETON = "exoskeleton"
    NEURAL_STIMULATOR = "neural_stimulator"
    COMPUTER_CURSOR = "computer_cursor"
    SMART_HOME = "smart_home"
    OTHER = "other"


class DeviceConnectionStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass(frozen=True)
class Device:
    id: str
    user_id: str
    name: str
    device_type: DeviceType
    connection_status: DeviceConnectionStatus
    capabilities: frozenset[str]
    last_command_timestamp: datetime | None
    domain_events: tuple[DomainEvent, ...] = field(default=())

    def execute_command(self, command: str, parameters: dict) -> "Device":
        return replace(
            self,
            last_command_timestamp=datetime.now(UTC),
            domain_events=self.domain_events
            + (
                DeviceCommandExecutedEvent(
                    aggregate_id=self.id,
                    occurred_at=datetime.now(UTC),
                    command=command,
                    parameters=parameters,
                ),
            ),
        )

    def mark_connected(self) -> "Device":
        return replace(
            self,
            connection_status=DeviceConnectionStatus.CONNECTED,
        )

    def mark_disconnected(self) -> "Device":
        return replace(
            self,
            connection_status=DeviceConnectionStatus.DISCONNECTED,
        )

    def supports_capability(self, capability: str) -> bool:
        return capability in self.capabilities
