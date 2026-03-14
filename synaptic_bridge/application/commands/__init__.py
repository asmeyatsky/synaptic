"""
Application Commands

Command handlers following CQRS pattern.
Each command is a separate class with a single responsibility.
"""

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any

from synaptic_bridge.domain.entities import Session, SessionStatus
from synaptic_bridge.domain.ports import SessionRepositoryPort, EventBusPort


@dataclass
class CreateSessionCommand:
    user_id: str
    device_ids: list[str]

    async def execute(
        self,
        session_repo: SessionRepositoryPort,
        event_bus: EventBusPort,
    ) -> Session:
        session = Session(
            id=f"session_{datetime.now(UTC).timestamp()}",
            user_id=self.user_id,
            status=SessionStatus.INITIATED,
            started_at=datetime.now(UTC),
            ended_at=None,
            device_ids=frozenset(self.device_ids),
            signal_count=0,
            classification_count=0,
        )

        await session_repo.save(session)
        await event_bus.publish(list(session.domain_events))

        return session


@dataclass
class StartSessionCommand:
    session_id: str

    async def execute(
        self,
        session_repo: SessionRepositoryPort,
        event_bus: EventBusPort,
    ) -> Session:
        session = await session_repo.get_by_id(self.session_id)
        if not session:
            raise ValueError(f"Session {self.session_id} not found")

        started_session = session.start()

        await session_repo.save(started_session)
        await event_bus.publish(list(started_session.domain_events))

        return started_session


@dataclass
class EndSessionCommand:
    session_id: str

    async def execute(
        self,
        session_repo: SessionRepositoryPort,
        event_bus: EventBusPort,
    ) -> Session:
        session = await session_repo.get_by_id(self.session_id)
        if not session:
            raise ValueError(f"Session {self.session_id} not found")

        completed_session = session.complete()

        await session_repo.save(completed_session)
        await event_bus.publish(list(completed_session.domain_events))

        return completed_session


@dataclass
class AcquireSignalCommand:
    session_id: str
    channels: list[str]

    async def execute(self, signal_repo: Any, event_bus: EventBusPort) -> Any:
        pass


@dataclass
class ClassifySignalCommand:
    signal_id: str

    async def execute(
        self, classifier: Any, signal_repo: Any, event_bus: EventBusPort
    ) -> Any:
        pass


@dataclass
class ConnectDeviceCommand:
    device_id: str

    async def execute(self, device_controller: Any) -> bool:
        return await device_controller.connect(self.device_id)


@dataclass
class DisconnectDeviceCommand:
    device_id: str

    async def execute(self, device_controller: Any) -> bool:
        return await device_controller.disconnect(self.device_id)


@dataclass
class SendDeviceCommandCommand:
    device_id: str
    command: str
    parameters: dict

    async def execute(self, device_controller: Any, device_repo: Any) -> bool:
        pass


@dataclass
class RegisterUserCommand:
    email: str
    name: str

    async def execute(
        self,
        user_repo: Any,
        event_bus: EventBusPort,
    ) -> Any:
        pass


@dataclass
class UpdatePreferencesCommand:
    user_id: str
    sampling_rate_hz: float | None = None
    classification_threshold: float | None = None

    async def execute(self, user_repo: Any, event_bus: EventBusPort) -> Any:
        pass
