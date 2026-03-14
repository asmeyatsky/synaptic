"""
Integration Tests

End-to-end tests for SynapticBridge API.
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from synaptic_bridge.presentation.api.main import app


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"


class TestSessionEndpoints:
    """Test session management endpoints."""

    @pytest.mark.asyncio
    async def test_create_session(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/sessions", json={"agent_id": "agent-1", "created_by": "admin"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            assert "execution_token" in data

    @pytest.mark.asyncio
    async def test_get_session(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            create_response = await client.post(
                "/sessions", json={"agent_id": "agent-1", "created_by": "admin"}
            )
            session_id = create_response.json()["session_id"]

            response = await client.get(f"/sessions/{session_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == session_id


class TestToolEndpoints:
    """Test tool management endpoints."""

    @pytest.mark.asyncio
    async def test_register_tool(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/tools",
                json={
                    "tool_name": "filesystem.read",
                    "version": "1.0.0",
                    "capabilities": ["read"],
                    "scope": "workspace:current",
                    "ttl_seconds": 900,
                    "network_egress": False,
                    "audit_level": "summary",
                    "signature": "test-sig",
                },
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_tools(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/tools")
            assert response.status_code == 200
            assert isinstance(response.json(), list)


class TestPolicyEndpoints:
    """Test policy management endpoints."""

    @pytest.mark.asyncio
    async def test_add_policy(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/policies",
                json={
                    "name": "Test Policy",
                    "description": "A test policy",
                    "rego_code": 'package test\ndeny { input.tool == "bad" }',
                    "effect": "deny",
                    "scope": "tool",
                    "tags": ["test"],
                },
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_policies(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/policies")
            assert response.status_code == 200


class TestCorrectionEndpoints:
    """Test correction capture endpoints."""

    @pytest.mark.asyncio
    async def test_capture_correction(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/corrections",
                json={
                    "session_id": "session-1",
                    "agent_id": "agent-1",
                    "original_intent": "read file",
                    "inferred_context": "user wants data",
                    "original_tool": "bad.tool",
                    "corrected_tool": "good.tool",
                    "operator_identity": "admin",
                    "confidence_before": 0.5,
                    "confidence_after": 0.9,
                },
            )
            assert response.status_code == 200
