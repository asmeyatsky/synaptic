"""
Dependency Injection Configuration

Following skill2026.md Rule 2 - Interface-First Development.
Wires implementations to ports at composition root.
"""

from typing import Any


class DependencyContainer:
    """
    Simple dependency injection container.

    Following skill2026.md - Dependency injection to manage dependencies.
    """

    def __init__(self):
        self._services: dict[str, Any] = {}
        self._factories: dict[str, callable] = {}

    def register(self, name: str, instance: Any) -> None:
        """Register a singleton instance."""
        self._services[name] = instance

    def register_factory(self, name: str, factory: callable) -> None:
        """Register a factory function for lazy instantiation."""
        self._factories[name] = factory

    def resolve(self, name: str) -> Any:
        """Resolve a service by name."""
        if name in self._services:
            return self._services[name]

        if name in self._factories:
            instance = self._factories[name]()
            self._services[name] = instance
            return instance

        raise KeyError(f"Service '{name}' not registered")


def create_container() -> DependencyContainer:
    """
    Create and configure the dependency container.

    Following skill2026.md - Composition root pattern.
    """
    from synaptic_bridge.infrastructure.repositories import (
        InMemorySignalRepository,
        InMemorySessionRepository,
        InMemoryUserRepository,
        InMemoryDeviceRepository,
    )
    from synaptic_bridge.infrastructure.adapters import (
        MockCognitiveClassifier,
        MockDeviceController,
        InMemoryEventBus,
    )

    container = DependencyContainer()

    container.register("signal_repo", InMemorySignalRepository())
    container.register("session_repo", InMemorySessionRepository())
    container.register("user_repo", InMemoryUserRepository())
    container.register("device_repo", InMemoryDeviceRepository())

    container.register("cognitive_classifier", MockCognitiveClassifier())
    container.register("device_controller", MockDeviceController())
    container.register("event_bus", InMemoryEventBus())

    return container
