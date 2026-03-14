"""
Infrastructure Adapters

Following skill2026.md Rule 2 - Interface-First Development.
Adapters implement ports defined in domain layer.
"""

from typing import Any
from datetime import datetime, UTC

from synaptic_bridge.domain.entities import (
    NeuralSignal,
    CognitiveState,
    CognitiveStateType,
    Device,
)
from synaptic_bridge.domain.value_objects import (
    ClassificationResult,
    DeviceStatus,
    DeviceCommand,
)


class MockCognitiveClassifier:
    """Mock implementation of CognitiveClassifierPort for testing."""

    async def classify(self, signal: NeuralSignal) -> ClassificationResult:
        import random

        states = ["focus", "relaxed", "stressed", "engaged"]
        state = random.choice(states)
        confidence = random.uniform(0.6, 0.95)

        return ClassificationResult(
            state_type=state,
            confidence=confidence,
            features_used=frozenset(["alpha", "beta", "theta"]),
            alternative_states=frozenset([s for s in states if s != state]),
        )

    async def train(
        self, user_id: str, signals: list[NeuralSignal], labels: list[str]
    ) -> None:
        pass


class MockDeviceController:
    """Mock implementation of DeviceControllerPort for testing."""

    def __init__(self):
        self._connected_devices: set[str] = set()

    async def connect(self, device_id: str) -> bool:
        self._connected_devices.add(device_id)
        return True

    async def disconnect(self, device_id: str) -> bool:
        self._connected_devices.discard(device_id)
        return True

    async def send_command(self, device: Device, command: DeviceCommand) -> bool:
        return True

    async def get_status(self, device_id: str) -> DeviceStatus:
        is_connected = device_id in self._connected_devices

        return DeviceStatus(
            device_id=device_id,
            is_connected=is_connected,
            last_update=datetime.now(UTC),
            state="operational" if is_connected else "disconnected",
            metrics=(
                ("battery_level", 85),
                ("signal_quality", 0.9),
            ),
        )


class InMemoryEventBus:
    """In-memory implementation of EventBusPort."""

    def __init__(self):
        self._handlers: dict[type, list[Any]] = {}
        self._published_events: list[Any] = []

    async def publish(self, events: list[Any]) -> None:
        self._published_events.extend(events)

        for event in events:
            event_type = type(event)
            if event_type in self._handlers:
                for handler in self._handlers[event_type]:
                    await handler(event)

    async def subscribe(self, event_type: type, handler: Any) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def get_published_events(self) -> list[Any]:
        return self._published_events.copy()
