"""
Policy Entity

Represents an OPA policy rule for governance.
Following PRD: Rego policies evaluated at dispatch time; policy violations are hard blocks.

Immutable domain model following skill2026.md Rule 3.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, UTC
from typing import FrozenSet
from enum import Enum

from ...domain.events import DomainEvent


class PolicyEffect(Enum):
    ALLOW = "allow"
    DENY = "deny"


class PolicyScope(Enum):
    TOOL = "tool"
    SESSION = "session"
    AGENT = "agent"
    NETWORK = "network"


@dataclass(frozen=True)
class Policy:
    policy_id: str
    name: str
    description: str
    rego_code: str
    effect: PolicyEffect
    scope: PolicyScope
    tags: FrozenSet[str]
    version: str
    enabled: bool
    created_at: datetime
    updated_at: datetime
    domain_events: tuple[DomainEvent, ...] = field(default=())

    def __post_init__(self):
        if not self.name:
            raise ValueError("Policy name is required")
        if not self.rego_code:
            raise ValueError("Rego code is required")

    def with_toggle(self, enabled: bool) -> "Policy":
        return replace(
            self,
            enabled=enabled,
            updated_at=datetime.now(UTC),
        )

    def with_version(self, new_version: str, new_rego: str) -> "Policy":
        return replace(
            self,
            version=new_version,
            rego_code=new_rego,
            updated_at=datetime.now(UTC),
        )

    def matches_tag(self, tag: str) -> bool:
        return tag in self.tags


@dataclass(frozen=True)
class PolicyViolation:
    violation_id: str
    policy_id: str
    session_id: str
    agent_id: str
    tool_name: str
    reason: str
    context: dict
    occurred_at: datetime

    def to_audit_dict(self) -> dict:
        return {
            "violation_id": self.violation_id,
            "policy_id": self.policy_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "tool_name": self.tool_name,
            "reason": self.reason,
            "context": self.context,
            "occurred_at": self.occurred_at.isoformat(),
        }
