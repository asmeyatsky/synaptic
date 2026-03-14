"""
SynapticBridge Domain Layer

Architectural Intent:
- Core business logic for MCP orchestration and CLE operations
- All domain models are immutable to ensure consistency
- Domain events used for cross-boundary communication
- Ports defined here for external dependencies

Bounded Contexts:
1. Tool Management - tool manifests, registry, capability contracts
2. Execution Fabric - execution tokens, session management, audit
3. Correction Learning Engine - patterns, corrections, predictive dispatch
4. Routing Intelligence - intent mapping, chain planning
5. Policy & Governance - OPA policies, drift detection

Following skill2026.md principles.
"""

from .entities import (
    ToolManifest,
    ExecutionSession,
    Correction,
    CorrectionPattern,
    Policy,
    AuditEvent,
    ToolCall,
    CapabilityType,
    AuditLevel,
    SessionStatus,
    ToolCallStatus,
    PolicyEffect,
    PolicyScope,
)
from .value_objects import (
    ExecutionToken,
    ToolResult,
    CorrectionScore,
    IntentEmbedding,
    PolicyRule,
)
from .events import (
    DomainEvent,
    ToolCalledEvent,
    CorrectionCapturedEvent,
    PolicyViolationEvent,
    SessionStartedEvent,
    SessionEndedEvent,
)
from .ports import (
    ToolRegistryPort,
    ExecutionPort,
    CorrectionStorePort,
    PolicyEnginePort,
    AuditLogPort,
    IntentClassifierPort,
    ChainPlannerPort,
    DriftDetectorPort,
)

__all__ = [
    "ToolManifest",
    "ExecutionSession",
    "Correction",
    "CorrectionPattern",
    "Policy",
    "AuditEvent",
    "ToolCall",
    "CapabilityType",
    "AuditLevel",
    "SessionStatus",
    "ToolCallStatus",
    "PolicyEffect",
    "PolicyScope",
    "ExecutionToken",
    "ToolResult",
    "CorrectionScore",
    "IntentEmbedding",
    "PolicyRule",
    "DomainEvent",
    "ToolCalledEvent",
    "CorrectionCapturedEvent",
    "PolicyViolationEvent",
    "SessionStartedEvent",
    "SessionEndedEvent",
    "ToolRegistryPort",
    "ExecutionPort",
    "CorrectionStorePort",
    "PolicyEnginePort",
    "AuditLogPort",
    "IntentClassifierPort",
    "ChainPlannerPort",
    "DriftDetectorPort",
]
