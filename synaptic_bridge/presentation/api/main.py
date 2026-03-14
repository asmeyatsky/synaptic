"""
SynapticBridge Presentation Layer

Architectural Intent:
- API controllers interact with application layer only
- No business logic in presentation layer
- Follows skill2026.md layer separation principles
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

from synaptic_bridge.infrastructure.config import create_container
from synaptic_bridge.infrastructure.mcp_servers import (
    SessionMCPServer,
    DeviceMCPServer,
    SignalMCPServer,
    UserMCPServer,
)

app = FastAPI(title="SynapticBridge API", version="1.0.0")

container = create_container()

session_server = SessionMCPServer(container)
device_server = DeviceMCPServer(container)
signal_server = SignalMCPServer(container)
user_server = UserMCPServer(container)


class CreateSessionRequest(BaseModel):
    user_id: str
    device_ids: list[str] = []


class StartSessionRequest(BaseModel):
    session_id: str


class EndSessionRequest(BaseModel):
    session_id: str


class ConnectDeviceRequest(BaseModel):
    device_id: str


class DeviceCommandRequest(BaseModel):
    device_id: str
    command_type: str
    parameters: dict = {}


@app.get("/")
async def root():
    return {"message": "SynapticBridge API", "version": "1.0.0"}


@app.post("/sessions")
async def create_session(request: CreateSessionRequest):
    """Create a new recording session."""
    try:
        result = await session_server.create_session(
            user_id=request.user_id,
            device_ids=request.device_ids,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/start")
async def start_session(request: StartSessionRequest):
    """Start an existing session."""
    try:
        result = await session_server.start_session(session_id=request.session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/end")
async def end_session(request: EndSessionRequest):
    """End an active session."""
    try:
        result = await session_server.end_session(session_id=request.session_id)
        return result
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


@app.get("/users/{user_id}/sessions")
async def list_user_sessions(user_id: str):
    """List all sessions for a user."""
    result = await session_server.list_user_sessions(user_id)
    return result


@app.post("/devices/connect")
async def connect_device(request: ConnectDeviceRequest):
    """Connect to a device."""
    try:
        result = await device_server.connect_device(device_id=request.device_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/devices/disconnect")
async def disconnect_device(request: ConnectDeviceRequest):
    """Disconnect from a device."""
    try:
        result = await device_server.disconnect_device(device_id=request.device_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/devices/command")
async def send_device_command(request: DeviceCommandRequest):
    """Send a command to a device."""
    try:
        result = await device_server.send_device_command(
            device_id=request.device_id,
            command_type=request.command_type,
            parameters=request.parameters,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get user by ID."""
    result = await user_server.get_user(user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result
