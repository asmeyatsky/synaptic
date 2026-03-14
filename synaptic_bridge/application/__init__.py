"""
SynapticBridge Application Layer

Architectural Intent:
- Use cases orchestrate domain objects via ports
- Command/Query separation following CQRS pattern
- DAG orchestration for multi-step workflows
- Parallel execution of independent operations

MCP Integration:
- Commands exposed as MCP tools (write operations)
- Queries exposed as MCP resources (read operations)
"""

from .commands import (
    CreateSessionCommand,
    StartSessionCommand,
    EndSessionCommand,
    AcquireSignalCommand,
    ClassifySignalCommand,
    ConnectDeviceCommand,
    DisconnectDeviceCommand,
    SendDeviceCommandCommand,
    RegisterUserCommand,
    UpdatePreferencesCommand,
)
from .queries import (
    GetSessionQuery,
    ListSessionsQuery,
    GetCognitiveStateQuery,
    ListCognitiveStatesQuery,
    GetDeviceQuery,
    ListDevicesQuery,
    GetUserQuery,
)
from .dtos import (
    SessionDTO,
    NeuralSignalDTO,
    CognitiveStateDTO,
    DeviceDTO,
    UserDTO,
    ClassificationResultDTO,
)
from .orchestration import (
    ProcessSignalWorkflow,
    DAGOrchestrator,
    WorkflowStep,
)

__all__ = [
    "CreateSessionCommand",
    "StartSessionCommand",
    "EndSessionCommand",
    "AcquireSignalCommand",
    "ClassifySignalCommand",
    "ConnectDeviceCommand",
    "DisconnectDeviceCommand",
    "SendDeviceCommandCommand",
    "RegisterUserCommand",
    "UpdatePreferencesCommand",
    "GetSessionQuery",
    "ListSessionsQuery",
    "GetCognitiveStateQuery",
    "ListCognitiveStatesQuery",
    "GetDeviceQuery",
    "ListDevicesQuery",
    "GetUserQuery",
    "SessionDTO",
    "NeuralSignalDTO",
    "CognitiveStateDTO",
    "DeviceDTO",
    "UserDTO",
    "ClassificationResultDTO",
    "ProcessSignalWorkflow",
    "DAGOrchestrator",
    "WorkflowStep",
]
