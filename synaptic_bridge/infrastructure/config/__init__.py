"""
Dependency Injection Configuration

Following skill2026.md Rule 2 - Interface-First Development.
Wires implementations to ports at composition root.
"""

from typing import Any


class DependencyContainer:
    """
    Simple dependency injection container.
    """

    def __init__(self):
        self._services: dict[str, Any] = {}
        self._factories: dict[str, callable] = {}

    def register(self, name: str, instance: Any) -> None:
        self._services[name] = instance

    def register_factory(self, name: str, factory: callable) -> None:
        self._factories[name] = factory

    def resolve(self, name: str) -> Any:
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
    """
    from synaptic_bridge.infrastructure.adapters import (
        InMemoryExecutionAdapter,
        InMemoryToolRegistry,
        InMemoryCorrectionStore,
        InMemoryPolicyEngine,
        InMemoryAuditLog,
        MockIntentClassifier,
    )

    container = DependencyContainer()

    container.register("execution_port", InMemoryExecutionAdapter())
    container.register("tool_registry", InMemoryToolRegistry())
    container.register("correction_store", InMemoryCorrectionStore())
    container.register("policy_engine", InMemoryPolicyEngine())
    container.register("audit_log", InMemoryAuditLog())
    container.register("intent_classifier", MockIntentClassifier())

    return container
