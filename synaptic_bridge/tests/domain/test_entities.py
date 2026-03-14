"""
Test Package

Following skill2026.md Rule 4 - Mandatory Testing Coverage.
Tests for all layers with appropriate mocking.
"""

import pytest
from unittest.mock import AsyncMock

from synaptic_bridge.domain.entities import (
    NeuralSignal,
    CognitiveState,
    CognitiveStateType,
    Session,
    SessionStatus,
    Device,
    DeviceType,
    DeviceConnectionStatus,
)
from synaptic_bridge.domain.value_objects import (
    UserPreferences,
    ClassificationResult,
    DeviceCommand,
)
from synaptic_bridge.infrastructure.adapters import InMemoryEventBus
from synaptic_bridge.infrastructure.config import create_container


class TestNeuralSignal:
    """Tests for NeuralSignal domain entity."""

    def test_create_neural_signal(self):
        signal = NeuralSignal(
            id="sig_1",
            session_id="session_1",
            channels=frozenset(["ch1", "ch2"]),
            samples=((1.0, 2.0), (3.0, 4.0)),
            sampling_rate_hz=250.0,
            timestamp=None,
        )

        assert signal.id == "sig_1"
        assert len(signal.channels) == 2
        assert len(signal.samples) == 2

    def test_get_channel_data(self):
        signal = NeuralSignal(
            id="sig_1",
            session_id="session_1",
            channels=frozenset(["ch1", "ch2"]),
            samples=((1.0, 2.0), (3.0, 4.0), (5.0, 6.0)),
            sampling_rate_hz=250.0,
            timestamp=None,
        )

        ch1_data = signal.get_channel_data("ch1")
        assert ch1_data == (1.0, 3.0, 5.0)

    def test_add_channel_creates_new_instance(self):
        signal = NeuralSignal(
            id="sig_1",
            session_id="session_1",
            channels=frozenset(["ch1"]),
            samples=((1.0,),),
            sampling_rate_hz=250.0,
            timestamp=None,
        )

        new_signal = signal.add_channel("ch2", (2.0,))

        assert "ch2" in new_signal.channels
        assert "ch1" in signal.channels
        assert signal != new_signal


class TestCognitiveState:
    """Tests for CognitiveState domain entity."""

    def test_create_cognitive_state(self):
        state = CognitiveState(
            id="cog_1",
            session_id="session_1",
            user_id="user_1",
            state_type=CognitiveStateType.FOCUS,
            confidence=0.85,
            features_used=frozenset(["alpha", "beta"]),
            timestamp=None,
        )

        assert state.state_type == CognitiveStateType.FOCUS
        assert state.confidence == 0.85
        assert state.is_reliable()

    def test_is_reliable_with_threshold(self):
        state = CognitiveState(
            id="cog_1",
            session_id="session_1",
            user_id="user_1",
            state_type=CognitiveStateType.FOCUS,
            confidence=0.5,
            features_used=frozenset(["alpha"]),
            timestamp=None,
        )

        assert not state.is_reliable(threshold=0.7)
        assert state.is_reliable(threshold=0.4)


class TestSession:
    """Tests for Session domain entity."""

    def test_create_session(self):
        session = Session(
            id="session_1",
            user_id="user_1",
            status=SessionStatus.INITIATED,
            started_at=None,
            ended_at=None,
            device_ids=frozenset(["device_1"]),
            signal_count=0,
            classification_count=0,
        )

        assert session.status == SessionStatus.INITIATED
        assert session.signal_count == 0

    def test_start_session(self):
        session = Session(
            id="session_1",
            user_id="user_1",
            status=SessionStatus.INITIATED,
            started_at=None,
            ended_at=None,
            device_ids=frozenset(),
            signal_count=0,
            classification_count=0,
        )

        started = session.start()

        assert started.status == SessionStatus.ACTIVE
        assert session != started

    def test_complete_session(self):
        from datetime import datetime, UTC

        session = Session(
            id="session_1",
            user_id="user_1",
            status=SessionStatus.ACTIVE,
            started_at=datetime.now(UTC),
            ended_at=None,
            device_ids=frozenset(),
            signal_count=5,
            classification_count=3,
        )

        completed = session.complete()

        assert completed.status == SessionStatus.COMPLETED
        assert completed.ended_at is not None
        assert completed.signal_count == 5


class TestDevice:
    """Tests for Device domain entity."""

    def test_create_device(self):
        device = Device(
            id="device_1",
            user_id="user_1",
            name="Robotic Arm",
            device_type=DeviceType.ROBOTIC_ARM,
            connection_status=DeviceConnectionStatus.DISCONNECTED,
            capabilities=frozenset(["move", "grip"]),
            last_command_timestamp=None,
        )

        assert device.name == "Robotic Arm"
        assert device.supports_capability("move")
        assert not device.supports_capability("invalid")


class TestUserPreferences:
    """Tests for UserPreferences value object."""

    def test_create_preferences(self):
        prefs = UserPreferences(
            sampling_rate_hz=500.0,
            enabled_channels=frozenset(["ch1", "ch2"]),
            classification_threshold=0.8,
        )

        assert prefs.sampling_rate_hz == 500.0
        assert prefs.classification_threshold == 0.8

    def test_with_sampling_rate(self):
        prefs = UserPreferences(sampling_rate_hz=250.0)
        new_prefs = prefs.with_sampling_rate(500.0)

        assert new_prefs.sampling_rate_hz == 500.0
        assert prefs.sampling_rate_hz == 250.0

    def test_with_threshold(self):
        prefs = UserPreferences(classification_threshold=0.7)
        new_prefs = prefs.with_threshold(0.9)

        assert new_prefs.classification_threshold == 0.9
        assert prefs.classification_threshold == 0.7


class TestInMemoryEventBus:
    """Tests for InMemoryEventBus."""

    @pytest.mark.asyncio
    async def test_publish_event(self):
        from dataclasses import dataclass
        from synaptic_bridge.domain.events import DomainEvent

        @dataclass(frozen=True)
        class TestEvent(DomainEvent):
            message: str = ""

        event_bus = InMemoryEventBus()

        event = TestEvent(aggregate_id="test_1", message="hello")
        await event_bus.publish([event])

        published = event_bus.get_published_events()
        assert len(published) == 1
        assert published[0].message == "hello"

    @pytest.mark.asyncio
    async def test_subscribe_and_receive(self):
        from dataclasses import dataclass
        from synaptic_bridge.domain.events import DomainEvent

        @dataclass(frozen=True)
        class TestEvent(DomainEvent):
            message: str = ""

        event_bus = InMemoryEventBus()
        received = []

        async def handler(event):
            received.append(event)

        await event_bus.subscribe(TestEvent, handler)

        event = TestEvent(aggregate_id="test_1", message="hello")
        await event_bus.publish([event])

        assert len(received) == 1
        assert received[0].message == "hello"


class TestDAGOrchestrator:
    """Tests for DAG-based workflow orchestration."""

    @pytest.mark.asyncio
    async def test_sequential_execution(self):
        from synaptic_bridge.application.orchestration import (
            DAGOrchestrator,
            WorkflowStep,
        )

        execution_order = []

        async def step_a(ctx, completed):
            execution_order.append("a")
            return "result_a"

        async def step_b(ctx, completed):
            execution_order.append("b")
            return "result_b"

        orchestrator = DAGOrchestrator(
            [
                WorkflowStep("a", step_a),
                WorkflowStep("b", step_b, depends_on=["a"]),
            ]
        )

        result = await orchestrator.execute({})

        assert execution_order == ["a", "b"]
        assert result["a"] == "result_a"
        assert result["b"] == "result_b"

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        from synaptic_bridge.application.orchestration import (
            DAGOrchestrator,
            WorkflowStep,
        )

        execution_times = {}

        async def step_a(ctx, completed):
            execution_times["a_start"] = len(execution_times)
            await asyncio.sleep(0.01)
            execution_times["a_end"] = len(execution_times)
            return "result_a"

        async def step_b(ctx, completed):
            execution_times["b_start"] = len(execution_times)
            await asyncio.sleep(0.01)
            execution_times["b_end"] = len(execution_times)
            return "result_b"

        orchestrator = DAGOrchestrator(
            [
                WorkflowStep("a", step_a),
                WorkflowStep("b", step_b),
            ]
        )

        result = await orchestrator.execute({})

        assert "a_start" in execution_times
        assert "b_start" in execution_times


import asyncio
