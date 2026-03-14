"""
Application Queries

Query handlers for SynapticBridge.
Following CQRS pattern.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class GetSessionQuery:
    session_id: str

    async def execute(self, execution_port: Any) -> Any:
        return await execution_port.get_session(self.session_id)


@dataclass
class ListToolsQuery:
    async def execute(self, tool_registry: Any) -> list[Any]:
        return await tool_registry.list_all()


@dataclass
class GetToolQuery:
    tool_name: str

    async def execute(self, tool_registry: Any) -> Any:
        return await tool_registry.get(self.tool_name)


@dataclass
class ListPoliciesQuery:
    async def execute(self, policy_engine: Any) -> list[Any]:
        return await policy_engine.list_policies()


@dataclass
class GetPolicyQuery:
    policy_id: str

    async def execute(self, policy_engine: Any) -> Any:
        policies = await policy_engine.list_policies()
        return next((p for p in policies if p.policy_id == self.policy_id), None)


@dataclass
class QueryAuditLogQuery:
    session_id: str | None = None
    event_type: str | None = None

    async def execute(self, audit_log: Any) -> list[Any]:
        filters = {}
        if self.session_id:
            filters["session_id"] = self.session_id
        if self.event_type:
            filters["event_type"] = self.event_type

        return await audit_log.query(filters)


@dataclass
class FindCorrectionPatternsQuery:
    intent_text: str

    async def execute(self, intent_classifier: Any, correction_store: Any) -> list[Any]:
        embedding = await intent_classifier.get_embedding(self.intent_text)
        return await correction_store.find_patterns(embedding)
