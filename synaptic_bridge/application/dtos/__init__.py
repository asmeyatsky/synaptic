"""
Application DTOs

Data Transfer Objects for layer communication.
Following skill2026.md structured output patterns.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class SessionDTO:
    id: str
    user_id: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    device_ids: list[str]
    signal_count: int
    classification_count: int

    @classmethod
    def from_entity(cls, entity: Any) -> "SessionDTO":
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            status=entity.status.value,
            started_at=entity.started_at,
            ended_at=entity.ended_at,
            device_ids=list(entity.device_ids),
            signal_count=entity.signal_count,
            classification_count=entity.classification_count,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "device_ids": self.device_ids,
            "signal_count": self.signal_count,
            "classification_count": self.classification_count,
        }


@dataclass
class NeuralSignalDTO:
    id: str
    session_id: str
    channels: list[str]
    sampling_rate_hz: float
    timestamp: datetime
    sample_count: int

    @classmethod
    def from_entity(cls, entity: Any) -> "NeuralSignalDTO":
        return cls(
            id=entity.id,
            session_id=entity.session_id,
            channels=list(entity.channels),
            sampling_rate_hz=entity.sampling_rate_hz,
            timestamp=entity.timestamp,
            sample_count=len(entity.samples),
        )


@dataclass
class CognitiveStateDTO:
    id: str
    session_id: str
    user_id: str
    state_type: str
    confidence: float
    timestamp: datetime

    @classmethod
    def from_entity(cls, entity: Any) -> "CognitiveStateDTO":
        return cls(
            id=entity.id,
            session_id=entity.session_id,
            user_id=entity.user_id,
            state_type=entity.state_type.value,
            confidence=entity.confidence,
            timestamp=entity.timestamp,
        )


@dataclass
class DeviceDTO:
    id: str
    user_id: str
    name: str
    device_type: str
    connection_status: str
    capabilities: list[str]
    last_command_timestamp: datetime | None

    @classmethod
    def from_entity(cls, entity: Any) -> "DeviceDTO":
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            name=entity.name,
            device_type=entity.device_type.value,
            connection_status=entity.connection_status.value,
            capabilities=list(entity.capabilities),
            last_command_timestamp=entity.last_command_timestamp,
        )


@dataclass
class UserDTO:
    id: str
    email: str
    name: str
    registered_at: datetime
    last_active_at: datetime

    @classmethod
    def from_entity(cls, entity: Any) -> "UserDTO":
        return cls(
            id=entity.id,
            email=entity.email,
            name=entity.name,
            registered_at=entity.registered_at,
            last_active_at=entity.last_active_at,
        )


@dataclass
class ClassificationResultDTO:
    state_type: str
    confidence: float
    features_used: list[str]
    is_reliable: bool

    @classmethod
    def from_entity(cls, entity: Any) -> "ClassificationResultDTO":
        return cls(
            state_type=entity.state_type,
            confidence=entity.confidence,
            features_used=list(entity.features_used),
            is_reliable=entity.is_reliable(),
        )
