"""
Portal API Routes

REST API endpoints for the SynapticBridge Admin Portal.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from synaptic_bridge.domain.constants import API_VERSION
from synaptic_bridge.infrastructure.config import create_container

logger = logging.getLogger("synaptic-bridge.portal")

router = APIRouter(prefix="/api/portal", tags=["portal"])

container = create_container()


class PolicyModel(BaseModel):
    id: str
    name: str
    resource: str
    action: str
    effect: str
    conditions: str | None = None
    enabled: bool = True


class AccessRequestModel(BaseModel):
    id: str
    requester: str
    tool: str
    justification: str | None = None
    status: str = "pending"
    requested_at: datetime


_policy_store: list[dict] = [
    {
        "id": "pol-001",
        "name": "Production Database Deletion",
        "resource": "database.tables",
        "action": "delete",
        "effect": "deny",
        "conditions": '{"env": "production"}',
        "enabled": True,
    },
    {
        "id": "pol-002",
        "name": "Costly AWS Operations",
        "resource": "aws.ec2",
        "action": "run_instances",
        "effect": "deny",
        "conditions": '{"requires_approval": true}',
        "enabled": True,
    },
    {
        "id": "pol-003",
        "name": "File System Read Only",
        "resource": "filesystem",
        "action": "write",
        "effect": "allow",
        "conditions": '{"allowed_dirs": ["/tmp", "/uploads"]}',
        "enabled": True,
    },
]

_access_requests: list[dict] = [
    {
        "id": "req-001",
        "requester": "Alice Chen",
        "tool": "aws.ec2.describe",
        "justification": "Need to check instance status for incident investigation",
        "status": "approved",
        "requested_at": datetime.now(UTC) - timedelta(hours=2),
    },
    {
        "id": "req-002",
        "requester": "Bob Smith",
        "tool": "database.query",
        "justification": "Running ad-hoc queries for the weekly report",
        "status": "pending",
        "requested_at": datetime.now(UTC) - timedelta(minutes=30),
    },
    {
        "id": "req-003",
        "requester": "Carol Davis",
        "tool": "git.push",
        "justification": "Need to push hotfix to production branch",
        "status": "pending",
        "requested_at": datetime.now(UTC) - timedelta(minutes=15),
    },
]

_corrections_store: list[dict] = [
    {
        "id": "cor-001",
        "original_tool": "bash.rm",
        "corrected_tool": "bash.mv_to_trash",
        "confidence": 0.85,
        "occurrence_count": 12,
        "status": "pending",
        "created_at": datetime.now(UTC) - timedelta(hours=1),
    },
    {
        "id": "cor-002",
        "original_tool": "aws.ec2.terminate",
        "corrected_tool": "aws.ec2.stop",
        "confidence": 0.92,
        "occurrence_count": 8,
        "status": "pending",
        "created_at": datetime.now(UTC) - timedelta(hours=3),
    },
    {
        "id": "cor-003",
        "original_tool": "http.get",
        "corrected_tool": "http.head",
        "confidence": 0.78,
        "occurrence_count": 5,
        "status": "approved",
        "created_at": datetime.now(UTC) - timedelta(days=1),
    },
    {
        "id": "cor-004",
        "original_tool": "sql.drop_table",
        "corrected_tool": "sql.soft_delete",
        "confidence": 0.95,
        "occurrence_count": 20,
        "status": "approved",
        "created_at": datetime.now(UTC) - timedelta(days=2),
    },
    {
        "id": "cor-005",
        "original_tool": "file.overwrite",
        "corrected_tool": "file.backup_and_write",
        "confidence": 0.65,
        "occurrence_count": 3,
        "status": "rejected",
        "created_at": datetime.now(UTC) - timedelta(days=3),
    },
]

_activity_log: list[dict] = [
    {
        "id": "act-001",
        "type": "session",
        "agent_id": "agent-alpha",
        "details": "New session created",
        "status": "success",
        "timestamp": datetime.now(UTC) - timedelta(minutes=5),
    },
    {
        "id": "act-002",
        "type": "tool",
        "agent_id": "agent-alpha",
        "details": "aws.s3.list_buckets executed",
        "status": "success",
        "timestamp": datetime.now(UTC) - timedelta(minutes=4),
    },
    {
        "id": "act-003",
        "type": "correction",
        "agent_id": "agent-beta",
        "details": "bash.rm → bash.mv_to_trash",
        "status": "success",
        "timestamp": datetime.now(UTC) - timedelta(minutes=2),
    },
    {
        "id": "act-004",
        "type": "tool",
        "agent_id": "agent-beta",
        "details": "aws.ec2.run_instances blocked by policy",
        "status": "blocked",
        "timestamp": datetime.now(UTC) - timedelta(minutes=1),
    },
]


@router.get("/health")
async def get_health():
    """Get system health status."""
    try:
        store = container.resolve("correction_store")
        has_conn = hasattr(store, "_conn") and store._conn is not None

        return {
            "status": "healthy",
            "version": API_VERSION,
            "service": "synaptic-bridge-portal",
            "dependencies": {
                "correction_store": "healthy" if has_conn else "healthy",
                "policy_engine": "healthy",
                "metrics": "healthy",
            },
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "version": API_VERSION,
            "service": "synaptic-bridge-portal",
            "dependencies": {},
        }


@router.get("/stats")
async def get_stats():
    """Get dashboard statistics."""
    pending = sum(1 for c in _corrections_store if c["status"] == "pending")
    approved = sum(1 for c in _corrections_store if c["status"] == "approved")
    rejected = sum(1 for c in _corrections_store if c["status"] == "rejected")

    total_corrections = pending + approved + rejected
    cle_accuracy = approved / total_corrections if total_corrections > 0 else 0.8

    return {
        "active_sessions": 3,
        "corrections_today": pending,
        "cle_accuracy": cle_accuracy,
        "active_policies": len(_policy_store),
    }


@router.get("/metrics")
async def get_metrics():
    """Get metrics data for charts."""
    hours = []
    for i in range(12, -1, -1):
        hours.append(
            {
                "label": f"{(datetime.now().hour - i) % 24}:00",
                "count": 50 + (i * 7) % 100,
            }
        )

    return {
        "request_volume": hours,
        "recent_activity": _activity_log[:5],
        "corrections_trend": [
            {"day": "Mon", "count": 12},
            {"day": "Tue", "count": 8},
            {"day": "Wed", "count": 15},
            {"day": "Thu", "count": 10},
            {"day": "Fri", "count": 6},
            {"day": "Sat", "count": 3},
            {"day": "Sun", "count": 4},
        ],
    }


@router.get("/activity")
async def get_activity(
    filter: str = Query("all", description="Filter by type: all, session, tool, correction"),
    search: str = Query("", description="Search term"),
):
    """Get activity log."""
    activities = _activity_log

    if filter != "all":
        activities = [a for a in activities if a["type"] == filter]

    if search:
        activities = [
            a
            for a in activities
            if search.lower() in a.get("details", "").lower()
            or search.lower() in a.get("agent_id", "").lower()
        ]

    return {"activities": activities}


@router.get("/corrections")
async def get_corrections(
    status: str = Query("pending", description="Filter by status: pending, approved, rejected"),
):
    """Get corrections list."""
    corrections = [c for c in _corrections_store if c["status"] == status]

    counts = {
        "pending": sum(1 for c in _corrections_store if c["status"] == "pending"),
        "approved": sum(1 for c in _corrections_store if c["status"] == "approved"),
        "rejected": sum(1 for c in _corrections_store if c["status"] == "rejected"),
    }

    return {"corrections": corrections, "counts": counts}


@router.post("/corrections/{correction_id}/approve")
async def approve_correction(correction_id: str):
    """Approve a correction."""
    for c in _corrections_store:
        if c["id"] == correction_id:
            c["status"] = "approved"
            return {"success": True, "correction": c}
    raise HTTPException(status_code=404, detail="Correction not found")


@router.post("/corrections/{correction_id}/reject")
async def reject_correction(correction_id: str):
    """Reject a correction."""
    for c in _corrections_store:
        if c["id"] == correction_id:
            c["status"] = "rejected"
            return {"success": True, "correction": c}
    raise HTTPException(status_code=404, detail="Correction not found")


@router.get("/policies")
async def get_policies():
    """Get policies list."""
    return {"policies": _policy_store}


@router.post("/policies")
async def create_policy(policy: dict):
    """Create a new policy."""
    new_policy = {
        "id": f"pol-{len(_policy_store) + 1:03d}",
        "name": policy.get("name", "Unnamed Policy"),
        "resource": policy.get("resource", ""),
        "action": policy.get("action", ""),
        "effect": policy.get("effect", "deny"),
        "conditions": policy.get("conditions"),
        "enabled": True,
    }
    _policy_store.append(new_policy)
    return {"success": True, "policy": new_policy}


@router.put("/policies/{policy_id}")
async def update_policy(policy_id: str, policy: dict):
    """Update a policy."""
    for p in _policy_store:
        if p["id"] == policy_id:
            p.update(
                {
                    "name": policy.get("name", p["name"]),
                    "resource": policy.get("resource", p["resource"]),
                    "action": policy.get("action", p["action"]),
                    "effect": policy.get("effect", p["effect"]),
                    "conditions": policy.get("conditions", p["conditions"]),
                }
            )
            return {"success": True, "policy": p}
    raise HTTPException(status_code=404, detail="Policy not found")


@router.post("/policies/{policy_id}/toggle")
async def toggle_policy(policy_id: str):
    """Toggle a policy enabled/disabled."""
    for p in _policy_store:
        if p["id"] == policy_id:
            p["enabled"] = not p["enabled"]
            return {"success": True, "policy": p}
    raise HTTPException(status_code=404, detail="Policy not found")


@router.get("/access-requests")
async def get_access_requests():
    """Get access requests list."""
    return {"requests": _access_requests}


@router.post("/access-requests")
async def create_access_request(request: dict):
    """Create a new access request."""
    new_request = {
        "id": f"req-{len(_access_requests) + 1:03d}",
        "requester": request.get("requester", "Unknown"),
        "tool": request.get("tool", ""),
        "justification": request.get("justification"),
        "status": "pending",
        "requested_at": datetime.now(UTC),
    }
    _access_requests.append(new_request)
    return {"success": True, "request": new_request}


@router.post("/access-requests/{request_id}/approve")
async def approve_access_request(request_id: str):
    """Approve an access request."""
    for r in _access_requests:
        if r["id"] == request_id:
            r["status"] = "approved"
            return {"success": True, "request": r}
    raise HTTPException(status_code=404, detail="Request not found")


@router.post("/access-requests/{request_id}/reject")
async def reject_access_request(request_id: str):
    """Reject an access request."""
    for r in _access_requests:
        if r["id"] == request_id:
            r["status"] = "rejected"
            return {"success": True, "request": r}
    raise HTTPException(status_code=404, detail="Request not found")
