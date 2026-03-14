"""
SynapticBridge Presentation Layer - FastAPI

REST API for SynapticBridge MCP orchestration platform.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

from synaptic_bridge.infrastructure.config import create_container
from synaptic_bridge.infrastructure.mcp_servers import (
    SessionMCPServer,
    ToolMCPServer,
    CLEMPServer,
    PolicyMCPServer,
)

app = FastAPI(
    title="SynapticBridge API",
    version="1.0.0",
    description="MCP Orchestration Platform with Correction Learning Engine",
)

container = create_container()

session_server = SessionMCPServer(container)
tool_server = ToolMCPServer(container)
cle_server = CLEMPServer(container)
policy_server = PolicyMCPServer(container)


class CreateSessionRequest(BaseModel):
    agent_id: str
    created_by: str


class ExecuteToolRequest(BaseModel):
    session_id: str
    tool_name: str
    parameters: dict = {}
    intent: str


class RegisterToolRequest(BaseModel):
    tool_name: str
    version: str
    capabilities: list[str]
    scope: str
    ttl_seconds: int = 900
    network_egress: bool = False
    audit_level: str = "summary"
    signature: str = ""


class CaptureCorrectionRequest(BaseModel):
    session_id: str
    agent_id: str
    original_intent: str
    inferred_context: str
    original_tool: str
    corrected_tool: str
    correction_metadata: dict = {}
    operator_identity: str
    confidence_before: float
    confidence_after: float


class AddPolicyRequest(BaseModel):
    name: str
    description: str
    rego_code: str
    effect: str
    scope: str
    tags: list[str] = []


@app.get("/")
async def root():
    return {
        "name": "SynapticBridge",
        "version": "1.0.0",
        "description": "MCP Orchestration Platform with Correction Learning Engine",
    }


@app.post("/sessions")
async def create_session(request: CreateSessionRequest):
    """Create a new agent execution session."""
    try:
        result = await session_server.create_session(
            agent_id=request.agent_id,
            created_by=request.created_by,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute")
async def execute_tool(request: ExecuteToolRequest):
    """Execute a tool with policy checks and CLE."""
    try:
        result = await session_server.execute_tool(
            session_id=request.session_id,
            tool_name=request.tool_name,
            parameters=request.parameters,
            intent=request.intent,
        )
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session by ID."""
    result = await session_server.get_session(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@app.post("/tools")
async def register_tool(request: RegisterToolRequest):
    """Register a new tool manifest."""
    try:
        result = await tool_server.register_tool(
            tool_name=request.tool_name,
            version=request.version,
            capabilities=request.capabilities,
            scope=request.scope,
            ttl_seconds=request.ttl_seconds,
            network_egress=request.network_egress,
            audit_level=request.audit_level,
            signature=request.signature,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools")
async def list_tools():
    """List all registered tools."""
    return await tool_server.list_tools()


@app.post("/corrections")
async def capture_correction(request: CaptureCorrectionRequest):
    """Capture a human override/correction."""
    try:
        result = await cle_server.capture_correction(
            session_id=request.session_id,
            agent_id=request.agent_id,
            original_intent=request.original_intent,
            inferred_context=request.inferred_context,
            original_tool=request.original_tool,
            corrected_tool=request.corrected_tool,
            correction_metadata=request.correction_metadata,
            operator_identity=request.operator_identity,
            confidence_before=request.confidence_before,
            confidence_after=request.confidence_after,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/policies")
async def add_policy(request: AddPolicyRequest):
    """Add a new OPA policy."""
    try:
        result = await policy_server.add_policy(
            name=request.name,
            description=request.description,
            rego_code=request.rego_code,
            effect=request.effect,
            scope=request.scope,
            tags=request.tags,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/policies")
async def list_policies():
    """List all policies."""
    return await policy_server.list_policies()
