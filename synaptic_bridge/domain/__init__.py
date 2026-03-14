"""
SynapticBridge Domain Layer

Architectural Intent:
- Core business logic for neural signal processing and BCI operations
- All domain models are immutable to ensure consistency
- Domain events used for cross-boundary communication
- Ports defined here for external dependencies (adapters in infrastructure)

Bounded Contexts:
1. Neural Signal Processing - signal acquisition and preprocessing
2. Cognitive Classification - mental state interpretation
3. Device Control - external device management
4. User Management - user profiles and settings

Parallelization Notes:
- Signal processing operations are parallelized across channels
- Classification can run concurrently with signal acquisition
"""

from .entities import (
    NeuralSignal,
    CognitiveState,
    Device,
    User,
    Session,
)
from .value_objects import (
    SignalChannel,
    SignalSample,
    ClassificationResult,
    DeviceCommand,
    DeviceStatus,
    UserPreferences,
)
from .events import (
    DomainEvent,
    SignalAcquiredEvent,
    ClassificationCompletedEvent,
    DeviceCommandExecutedEvent,
    SessionStartedEvent,
    SessionEndedEvent,
)
from .ports import (
    SignalRepositoryPort,
    CognitiveClassifierPort,
    DeviceControllerPort,
    UserRepositoryPort,
    EventBusPort,
)

__all__ = [
    "NeuralSignal",
    "CognitiveState",
    "Device",
    "User",
    "Session",
    "SignalChannel",
    "SignalSample",
    "ClassificationResult",
    "DeviceCommand",
    "DeviceStatus",
    "UserPreferences",
    "DomainEvent",
    "SignalAcquiredEvent",
    "ClassificationCompletedEvent",
    "DeviceCommandExecutedEvent",
    "SessionStartedEvent",
    "SessionEndedEvent",
    "SignalRepositoryPort",
    "CognitiveClassifierPort",
    "DeviceControllerPort",
    "UserRepositoryPort",
    "EventBusPort",
]
