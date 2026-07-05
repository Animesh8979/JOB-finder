"""Model Context Protocol (MCP) Client Manager.

This module provides a unified interface to start and communicate with
local MCP servers using stdio (e.g. Memory, Sequential Thinking, Research).

All errors are silently absorbed — MCP is a best-effort enhancement layer.
If servers fail to start, tools fail to list, or calls fail, the caller
gets an empty result and the app continues without MCP.
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-guard the heavy MCP imports so a missing or broken package never
# crashes the rest of the application.
# ---------------------------------------------------------------------------
_MCP_AVAILABLE = False
try:
    import nest_asyncio
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import CallToolResult
    nest_asyncio.apply()
    _MCP_AVAILABLE = True
except Exception:
    # mcp or nest_asyncio not installed / broken — every public function
    # will gracefully return empty results.
    pass


class MCPManager:
    """Manages connections to multiple MCP servers."""

    def __init__(self) -> None:
        self.sessions: Dict[str, Any] = {}
        self.exit_stack: Optional[AsyncExitStack] = AsyncExitStack() if _MCP_AVAILABLE else None
        self._tool_to_server: Dict[str, str] = {}

    async def connect_to_server(
        self,
        server_id: str,
        command: str,
        args: List[str],
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        """Connect to a local MCP server via stdio.  Never raises."""
        if not _MCP_AVAILABLE or self.exit_stack is None:
            return

        # Resolve the command to a real executable path (fixes Windows .cmd issues)
        resolved = shutil.which(command)
        if not resolved:
            logger.debug("MCP: skipping '%s' — command '%s' not on PATH", server_id, command)
            return

        server_params = StdioServerParameters(command=resolved, args=args, env=env)

        try:
            transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = transport
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self.sessions[server_id] = session

            # Map every tool this server exposes → server_id
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                self._tool_to_server[tool.name] = server_id

            logger.debug("MCP: connected to '%s' (%d tools)", server_id, len(tools_response.tools))
        except Exception:
            # Connection failed — absorb silently.  The server simply won't
            # be available; downstream code falls back to native paths.
            logger.debug("MCP: failed to connect to '%s' (silenced)", server_id, exc_info=True)

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools across connected servers.  Never raises."""
        all_tools: List[Dict[str, Any]] = []
        for server_id, session in list(self.sessions.items()):
            try:
                response = await session.list_tools()
                for tool in response.tools:
                    all_tools.append({
                        "name": tool.name,
                        "description": tool.description or "",
                        "input_schema": tool.inputSchema,
                    })
            except Exception:
                logger.debug("MCP: error listing tools for '%s' (silenced)", server_id, exc_info=True)
        return all_tools

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call a specific tool by name.  Returns '' on any failure."""
        server_id = self._tool_to_server.get(tool_name)
        if not server_id or server_id not in self.sessions:
            return ""

        try:
            result: CallToolResult = await self.sessions[server_id].call_tool(tool_name, arguments=arguments)
            output = "".join(
                block.text + "\n" for block in result.content if getattr(block, "type", "") == "text"
            )
            if result.isError:
                return ""
            return output.strip()
        except Exception:
            logger.debug("MCP: error calling tool '%s' (silenced)", tool_name, exc_info=True)
            return ""

    async def cleanup(self) -> None:
        """Close all connections.  Never raises."""
        try:
            if self.exit_stack:
                await self.exit_stack.aclose()
        except Exception:
            pass
        self.sessions.clear()
        self._tool_to_server.clear()


# ---------------------------------------------------------------------------
# Global singleton + sync wrappers
# ---------------------------------------------------------------------------
_global_manager: Optional[MCPManager] = None


def _get_loop() -> asyncio.AbstractEventLoop:
    """Get or create an event loop for the current thread."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("closed")
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def get_manager() -> MCPManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = MCPManager()
    return _global_manager


def start_servers() -> None:
    """Start the standard suite of MCP servers.  Never raises."""
    if not _MCP_AVAILABLE:
        return

    manager = get_manager()
    loop = _get_loop()

    async def _start() -> None:
        env = os.environ.copy()

        # --- Always-available servers (no API key needed) ---
        await manager.connect_to_server("memory", "npx", ["-y", "@modelcontextprotocol/server-memory"])
        await manager.connect_to_server("sequential-thinking", "npx", ["-y", "@modelcontextprotocol/server-sequential-thinking"])
        await manager.connect_to_server("playwright", "npx", ["-y", "@playwright/mcp"])
        await manager.connect_to_server("sqlite", "uvx", ["mcp-server-sqlite", "--db-path", "jobs.db"])

        # --- Sub-Agents ---
        env_sa = env.copy()
        if "AGENTS_DIR" not in env_sa:
            env_sa["AGENTS_DIR"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents"))
        await manager.connect_to_server("sub-agents", "npx", ["-y", "sub-agents-mcp"], env=env_sa)

        # --- API-key-gated servers (skip silently if key missing) ---
        if env.get("GITHUB_PERSONAL_ACCESS_TOKEN"):
            await manager.connect_to_server("github", "npx", ["-y", "@modelcontextprotocol/server-github"], env=env)

        if env.get("BRAVE_API_KEY"):
            await manager.connect_to_server("brave-search", "npx", ["-y", "@modelcontextprotocol/server-brave-search"], env=env)

        if env.get("TAVILY_API_KEY"):
            await manager.connect_to_server("deep-research", "npx", ["-y", "mcp-deep-research@latest"], env=env)

        if env.get("FIRECRAWL_API_KEY"):
            await manager.connect_to_server("firecrawl", "npx", ["-y", "@mendable/firecrawl-mcp-server"], env=env)

    try:
        loop.run_until_complete(_start())
    except Exception:
        logger.debug("MCP: start_servers() failed (silenced)", exc_info=True)


def get_available_tools() -> List[Dict[str, Any]]:
    """Synchronous wrapper.  Returns [] on any failure."""
    if not _MCP_AVAILABLE:
        return []
    try:
        return _get_loop().run_until_complete(get_manager().list_tools())
    except Exception:
        return []


def call_tool(tool_name: str, arguments: dict) -> str:
    """Synchronous wrapper.  Returns '' on any failure."""
    if not _MCP_AVAILABLE:
        return ""
    try:
        return _get_loop().run_until_complete(get_manager().call_tool(tool_name, arguments))
    except Exception:
        return ""
