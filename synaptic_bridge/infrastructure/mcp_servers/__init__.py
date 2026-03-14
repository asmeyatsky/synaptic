"""
MCP Servers

Following skill2026.md Pattern 1 - Bounded Context as MCP Server.
Each bounded context exposed as MCP server with:
- Tools = write operations (commands)
- Resources = read operations (queries)
- Prompts = reusable interaction patterns
"""

from typing import Any
from datetime import datetime, UTC

from synaptic_bridge.domain.entities import (
    Session,
    SessionStatus,
    Device,
    DeviceType,
    DeviceConnectionStatus,
)
from synaptic_bridge.application.commands import (
    CreateSessionCommand,
    StartSessionCommand,
    EndSessionCommand,
)
from synaptic_bridge.application.queries import GetSessionQuery, ListSessionsQuery
from synaptic_bridge.application.dtos import SessionDTO


class SessionMCPServer:
    """
    MCP server for Session bounded context.

    Tools:
    - create_session: Create a new recording session
    - start_session: Start an existing session
    - end_session: End an active session

    Resources:
    - session://{id}: Get session by ID
    - sessions://user/{user_id}: List user's sessions
    """

    def __init__(self, container: Any):
        self._container = container

    async def create_session(self, user_id: str, device_ids: list[str]) -> dict:
        """Create a new recording session."""
        command = CreateSessionCommand(user_id=user_id, device_ids=device_ids)

        session_repo = self._container.resolve("session_repo")
        event_bus = self._container.resolve("event_bus")

        session = await command.execute(session_repo, event_bus)

        return SessionDTO.from_entity(session).to_dict()

    async def start_session(self, session_id: str) -> dict:
        """Start an existing session."""
        command = StartSessionCommand(session_id=session_id)

        session_repo = self._container.resolve("session_repo")
        event_bus = self._container.resolve("event_bus")

        session = await command.execute(session_repo, event_bus)

        return SessionDTO.from_entity(session).to_dict()

    async def end_session(self, session_id: str) -> dict:
        """End an active session."""
        command = EndSessionCommand(session_id=session_id)

        session_repo = self._container.resolve("session_repo")
        event_bus = self._container.resolve("event_bus")

        session = await command.execute(session_repo, event_bus)

        return SessionDTO.from_entity(session).to_dict()

    async def get_session(self, session_id: str) -> dict | None:
        """Get session by ID (resource handler)."""
        query = GetSessionQuery(session_id=session_id)
        session_repo = self._container.resolve("session_repo")

        session = await query.execute(session_repo)

        if session:
            return SessionDTO.from_entity(session).to_dict()
        return None

    async def list_user_sessions(self, user_id: str) -> list[dict]:
        """List all sessions for a user (resource handler)."""
        query = ListSessionsQuery(user_id=user_id)
        session_repo = self._container.resolve("session_repo")

        sessions = await query.execute(session_repo)

        return [SessionDTO.from_entity(s).to_dict() for s in sessions]


class DeviceMCPServer:
    """
    MCP server for Device bounded context.

    Tools:
    - connect_device: Connect to a device
    - disconnect_device: Disconnect from a device
    - send_device_command: Send command to device

    Resources:
    - device://{id}: Get device by ID
    - devices://user/{user_id}: List user's devices
    """

    def __init__(self, container: Any):
        self._container = container

    async def connect_device(self, device_id: str) -> dict:
        """Connect to a device."""
        controller = self._container.resolve("device_controller")

        success = await controller.connect(device_id)

        return {"success": success, "device_id": device_id}

    async def disconnect_device(self, device_id: str) -> dict:
        """Disconnect from a device."""
        controller = self._container.resolve("device_controller")

        success = await controller.disconnect(device_id)

        return {"success": success, "device_id": device_id}

    async def send_device_command(
        self, device_id: str, command_type: str, parameters: dict
    ) -> dict:
        """Send a command to a device."""
        from synaptic_bridge.domain.value_objects import DeviceCommand

        controller = self._container.resolve("device_controller")
        device_repo = self._container.resolve("device_repo")

        device = await device_repo.get_by_id(device_id)
        if not device:
            raise ValueError(f"Device {device_id} not found")

        param_tuples = tuple(parameters.items())
        command = DeviceCommand(
            command_type=command_type,
            parameters=param_tuples,
            issued_at=datetime.now(UTC),
            issued_by=device.user_id,
        )

        success = await controller.send_command(device, command)

        return {"success": success, "device_id": device_id, "command": command_type}


class SignalMCPServer:
    """
    MCP server for Signal Processing bounded context.

    Tools:
    - process_signal: Process neural signal and classify

    Resources:
    - signal://{id}: Get signal by ID
    - signals://session/{session_id}: List session signals
    """

    def __init__(self, container: Any):
        self._container = container

    async def process_signal(self, signal_id: str) -> dict:
        """Process neural signal and return classification."""
        signal_repo = self._container.resolve("signal_repo")
        classifier = self._container.resolve("cognitive_classifier")

        signal = await signal_repo.get_by_id(signal_id)
        if not signal:
            raise ValueError(f"Signal {signal_id} not found")

        result = await classifier.classify(signal)

        return {
            "signal_id": signal_id,
            "state_type": result.state_type,
            "confidence": result.confidence,
            "features_used": list(result.features_used),
            "is_reliable": result.is_reliable(),
        }


class UserMCPServer:
    """
    MCP server for User bounded context.

    Tools:
    - register_user: Register a new user
    - update_preferences: Update user preferences

    Resources:
    - user://{id}: Get user by ID
    """

    def __init__(self, container: Any):
        self._container = container

    async def get_user(self, user_id: str) -> dict | None:
        """Get user by ID (resource handler)."""
        from synaptic_bridge.application.queries import GetUserQuery
        from synaptic_bridge.application.dtos import UserDTO

        query = GetUserQuery(user_id=user_id)
        user_repo = self._container.resolve("user_repo")

        user = await query.execute(user_repo)

        if user:
            return UserDTO.from_entity(user).to_dict()
        return None
