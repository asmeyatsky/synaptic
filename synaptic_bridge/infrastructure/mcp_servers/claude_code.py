"""
Claude Code MCP Integration

Following PRD Phase 4: Claude Code native SynapticBridge MCP server integration.
Provides native MCP server for Claude Code to connect to SynapticBridge.
"""

import asyncio
import json
import sys
from typing import Any
from dataclasses import dataclass
from enum import Enum


class MCPMessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


@dataclass
class MCPMessage:
    jsonrpc: str = "2.0"
    id: str | None = None
    method: str | None = None
    params: dict | None = None
    result: Any = None
    error: dict | None = None


class ClaudeCodeMCPServer:
    """
    Claude Code native MCP server integration.

    Following PRD Phase 4: Claude Code native SynapticBridge MCP server integration.
    Communicates via STDIO following MCP spec.
    """

    def __init__(self):
        self._tools = {}
        self._resources = {}
        self._handlers = {}
        self._request_id = 0
        self._initialized = False

    def register_tool(
        self, name: str, handler: callable, description: str, input_schema: dict
    ) -> None:
        """Register a tool for Claude Code to use."""
        self._tools[name] = {
            "handler": handler,
            "description": description,
            "inputSchema": input_schema,
        }

    def register_resource(
        self, uri: str, handler: callable, mime_type: str = "application/json"
    ) -> None:
        """Register a resource for Claude Code to access."""
        self._resources[uri] = {
            "handler": handler,
            "mimeType": mime_type,
        }

    def initialize(self) -> None:
        """Initialize the MCP server with tools and resources."""
        from synaptic_bridge.infrastructure.config import create_container
        from synaptic_bridge.infrastructure.adapters.intent_classifier import (
            IntentClassifier,
        )
        from synaptic_bridge.infrastructure.adapters.drift_detector import DriftDetector

        container = create_container()

        self.register_tool(
            "synaptic_create_session",
            self._create_session_handler(container),
            "Create a new SynapticBridge execution session",
            {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Agent ID"},
                    "created_by": {"type": "string", "description": "Creator ID"},
                },
                "required": ["agent_id", "created_by"],
            },
        )

        self.register_tool(
            "synaptic_execute_tool",
            self._execute_tool_handler(container),
            "Execute a tool through SynapticBridge with policy checks",
            {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                    "tool_name": {"type": "string", "description": "Tool name"},
                    "parameters": {"type": "object", "description": "Tool parameters"},
                    "intent": {"type": "string", "description": "Intent description"},
                },
                "required": ["session_id", "tool_name", "intent"],
            },
        )

        self.register_tool(
            "synaptic_capture_correction",
            self._capture_correction_handler(container),
            "Capture a human correction for CLE learning",
            {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "agent_id": {"type": "string"},
                    "original_intent": {"type": "string"},
                    "original_tool": {"type": "string"},
                    "corrected_tool": {"type": "string"},
                    "operator_identity": {"type": "string"},
                    "confidence_before": {"type": "number"},
                    "confidence_after": {"type": "number"},
                },
                "required": ["session_id", "original_tool", "corrected_tool"],
            },
        )

        self.register_tool(
            "synaptic_list_tools",
            self._list_tools_handler(container),
            "List all registered tools",
            {"type": "object", "properties": {}},
        )

        self.register_tool(
            "synaptic_add_policy",
            self._add_policy_handler(container),
            "Add an OPA policy",
            {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "rego_code": {"type": "string"},
                    "effect": {"type": "string", "enum": ["allow", "deny"]},
                    "scope": {
                        "type": "string",
                        "enum": ["tool", "session", "agent", "network"],
                    },
                },
                "required": ["name", "rego_code", "effect"],
            },
        )

        self.register_tool(
            "synaptic_query_logs",
            self._query_logs_handler(container),
            "Query audit logs",
            {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "event_type": {"type": "string"},
                    "limit": {"type": "integer", "default": 100},
                },
            },
        )

        self.register_resource(
            "synaptic://sessions",
            self._sessions_resource_handler(container),
            "application/json",
        )

        self.register_resource(
            "synaptic://tools",
            self._tools_resource_handler(container),
            "application/json",
        )

        self.register_resource(
            "synaptic://policies",
            self._policies_resource_handler(container),
            "application/json",
        )

        self._initialized = True

    def _create_session_handler(self, container):
        async def handler(params: dict) -> dict:
            from synaptic_bridge.application.commands import CreateSessionCommand

            cmd = CreateSessionCommand(
                agent_id=params["agent_id"],
                created_by=params["created_by"],
            )
            execution_port = container.resolve("execution_port")
            audit_log = container.resolve("audit_log")
            session = await cmd.execute(execution_port, audit_log)
            return {
                "session_id": session.session_id,
                "token": session.execution_token,
                "expires_at": str(session.expires_at),
            }

        return handler

    def _execute_tool_handler(self, container):
        async def handler(params: dict) -> dict:
            from synaptic_bridge.application.commands import ExecuteToolCommand

            cmd = ExecuteToolCommand(
                session_id=params["session_id"],
                tool_name=params["tool_name"],
                parameters=params.get("parameters", {}),
                intent=params["intent"],
            )
            execution_port = container.resolve("execution_port")
            tool_registry = container.resolve("tool_registry")
            policy_engine = container.resolve("policy_engine")
            audit_log = container.resolve("audit_log")
            return await cmd.execute(
                execution_port, tool_registry, policy_engine, audit_log
            )

        return handler

    def _capture_correction_handler(self, container):
        async def handler(params: dict) -> dict:
            from synaptic_bridge.application.commands import CaptureCorrectionCommand

            cmd = CaptureCorrectionCommand(
                session_id=params.get("session_id", ""),
                agent_id=params.get("agent_id", ""),
                original_intent=params.get("original_intent", ""),
                inferred_context=params.get("inferred_context", ""),
                original_tool=params["original_tool"],
                corrected_tool=params["corrected_tool"],
                correction_metadata=params.get("correction_metadata", {}),
                operator_identity=params.get("operator_identity", "claude"),
                confidence_before=params.get("confidence_before", 0.5),
                confidence_after=params.get("confidence_after", 0.9),
            )
            correction_store = container.resolve("correction_store")
            return await cmd.execute(correction_store)

        return handler

    def _list_tools_handler(self, container):
        async def handler(params: dict) -> dict:
            tool_registry = container.resolve("tool_registry")
            tools = await tool_registry.list_all()
            return [{"name": t.tool_name, "version": t.version} for t in tools]

        return handler

    def _add_policy_handler(self, container):
        async def handler(params: dict) -> dict:
            from synaptic_bridge.application.commands import AddPolicyCommand
            from synaptic_bridge.domain.entities import PolicyEffect, PolicyScope

            cmd = AddPolicyCommand(
                name=params["name"],
                description=params.get("description", ""),
                rego_code=params["rego_code"],
                effect=PolicyEffect(params["effect"]),
                scope=PolicyScope(params.get("scope", "tool")),
                tags=params.get("tags", []),
            )
            policy_engine = container.resolve("policy_engine")
            result = await cmd.execute(policy_engine)
            return {"policy_id": result.policy_id, "name": result.name}

        return handler

    def _query_logs_handler(self, container):
        async def handler(params: dict) -> dict:
            audit_log = container.resolve("audit_log")
            filters = {}
            if params.get("session_id"):
                filters["session_id"] = params["session_id"]
            events = await audit_log.query(filters)
            limit = params.get("limit", 100)
            return [
                {"event_id": e.event_id, "type": e.event_type} for e in events[:limit]
            ]

        return handler

    def _sessions_resource_handler(self, container):
        async def handler() -> str:
            execution_port = container.resolve("execution_port")
            return json.dumps({"note": "Use synaptic_create_session tool"})

        return handler

    def _tools_resource_handler(self, container):
        async def handler() -> str:
            tool_registry = container.resolve("tool_registry")
            tools = await tool_registry.list_all()
            return json.dumps(
                [{"name": t.tool_name, "version": t.version} for t in tools]
            )

        return handler

    def _policies_resource_handler(self, container):
        async def handler() -> str:
            policy_engine = container.resolve("policy_engine")
            policies = await policy_engine.list_policies()
            return json.dumps([{"id": p.policy_id, "name": p.name} for p in policies])

        return handler

    async def handle_message(self, message: dict) -> dict:
        """Handle incoming MCP message from Claude Code."""
        msg_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {"subscribe": True, "listChanged": True},
                    },
                    "serverInfo": {
                        "name": "synaptic-bridge",
                        "version": "1.0.0",
                    },
                },
            }

        if method == "tools/list":
            tools = [
                {
                    "name": name,
                    "description": info["description"],
                    "inputSchema": info["inputSchema"],
                }
                for name, info in self._tools.items()
            ]
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": tools}}

        if method == "tools/call":
            tool_name = params.get("name")
            tool_params = params.get("arguments", {})

            if tool_name in self._tools:
                handler = self._tools[tool_name]["handler"]
                result = await handler(tool_params)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result)}]
                    },
                }

        if method == "resources/list":
            resources = [
                {"uri": uri, "mimeType": info["mimeType"]}
                for uri, info in self._resources.items()
            ]
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"resources": resources}}

        if method == "resources/read":
            uri = params.get("uri")
            if uri in self._resources:
                handler = self._resources[uri]["handler"]
                content = await handler()
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": self._resources[uri]["mimeType"],
                                "text": content,
                            }
                        ]
                    },
                }

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": "Method not found"},
        }

    async def run(self):
        """Run the MCP server - reads from stdin, writes to stdout."""
        self.initialize()

        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                if not line:
                    break

                message = json.loads(line.strip())
                response = await self.handle_message(message)

                if response:
                    print(json.dumps(response), flush=True)

            except json.JSONDecodeError:
                continue
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": str(e)},
                }
                print(json.dumps(error_response), flush=True)


def main():
    """Entry point for Claude Code MCP server."""
    server = ClaudeCodeMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
