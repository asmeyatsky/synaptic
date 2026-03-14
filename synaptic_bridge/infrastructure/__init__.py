"""
SynapticBridge Infrastructure Layer

Architectural Intent:
- Implements ports defined in domain layer
- MCP servers expose bounded contexts to AI agents
- Infrastructure has ZERO business logic (Rule 1)
- Adapters wrapped behind ports for testability

MCP Integration:
- Each bounded context exposed as MCP server
- Tools = write operations, Resources = read operations
"""

from .repositories import (
    InMemorySignalRepository,
    InMemorySessionRepository,
    InMemoryUserRepository,
    InMemoryDeviceRepository,
)
from .adapters import (
    MockCognitiveClassifier,
    MockDeviceController,
    InMemoryEventBus,
)
from .mcp_servers import (
    SessionMCPServer,
    SignalMCPServer,
    DeviceMCPServer,
    UserMCPServer,
)
from .config import (
    DependencyContainer,
    create_container,
)

__all__ = [
    "InMemorySignalRepository",
    "InMemorySessionRepository",
    "InMemoryUserRepository",
    "InMemoryDeviceRepository",
    "MockCognitiveClassifier",
    "MockDeviceController",
    "InMemoryEventBus",
    "SessionMCPServer",
    "SignalMCPServer",
    "DeviceMCPServer",
    "UserMCPServer",
    "DependencyContainer",
    "create_container",
]
