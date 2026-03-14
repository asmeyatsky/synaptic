"""
Repository Implementations

Following skill2026.md Rule 1 - Zero Business Logic in Infrastructure.
Repositories only persist/retrieve data, no business rules.
"""

from typing import Any
from datetime import datetime, UTC

from synaptic_bridge.domain.entities import NeuralSignal, Session, User, Device
from synaptic_bridge.domain.ports import (
    SignalRepositoryPort,
    SessionRepositoryPort,
    UserRepositoryPort,
)
from synaptic_bridge.domain.value_objects import UserPreferences


class InMemorySignalRepository:
    """In-memory implementation of SignalRepositoryPort."""

    def __init__(self):
        self._signals: dict[str, NeuralSignal] = {}

    async def save(self, signal: NeuralSignal) -> None:
        self._signals[signal.id] = signal

    async def get_by_id(self, signal_id: str) -> NeuralSignal | None:
        return self._signals.get(signal_id)

    async def get_by_session(self, session_id: str) -> list[NeuralSignal]:
        return [s for s in self._signals.values() if s.session_id == session_id]

    async def delete(self, signal_id: str) -> None:
        self._signals.pop(signal_id, None)


class InMemorySessionRepository:
    """In-memory implementation of SessionRepositoryPort."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    async def save(self, session: Session) -> None:
        self._sessions[session.id] = session

    async def get_by_id(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    async def get_by_user(self, user_id: str) -> list[Session]:
        return [s for s in self._sessions.values() if s.user_id == user_id]

    async def get_active_session(self, user_id: str) -> Session | None:
        from synaptic_bridge.domain.entities import SessionStatus

        for s in self._sessions.values():
            if s.user_id == user_id and s.status == SessionStatus.ACTIVE:
                return s
        return None


class InMemoryUserRepository:
    """In-memory implementation of UserRepositoryPort."""

    def __init__(self):
        self._users: dict[str, User] = {}
        self._email_index: dict[str, str] = {}

    async def save(self, user: User) -> None:
        self._users[user.id] = user
        self._email_index[user.email] = user.id

    async def get_by_id(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        user_id = self._email_index.get(email)
        return self._users.get(user_id) if user_id else None

    async def delete(self, user_id: str) -> None:
        user = self._users.pop(user_id, None)
        if user:
            self._email_index.pop(user.email, None)


class InMemoryDeviceRepository:
    """In-memory storage for devices."""

    def __init__(self):
        self._devices: dict[str, Device] = {}

    async def save(self, device: Device) -> None:
        self._devices[device.id] = device

    async def get_by_id(self, device_id: str) -> Device | None:
        return self._devices.get(device_id)

    async def get_by_user(self, user_id: str) -> list[Device]:
        return [d for d in self._devices.values() if d.user_id == user_id]

    async def delete(self, device_id: str) -> None:
        self._devices.pop(device_id, None)
