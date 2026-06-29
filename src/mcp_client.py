"""Model Context Protocol (MCP) Client Manager.

This module provides a unified interface to start and communicate with
local MCP servers using stdio (e.g. Memory, Sequential Thinking, Research).
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

import nest_asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult

# Apply nest_asyncio to allow asyncio.run() within Streamlit/FastAPI loops
nest_asyncio.apply()

logger = logging.getLogger(__name__)


class MCPManager:
    """Manages connections to multiple MCP servers."""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self._tool_to_server: Dict[str, str] = {}
        
    async def connect_to_server(self, server_id: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        """Connect to a local MCP server via stdio."""
        logger.info(f"Connecting to MCP server '{server_id}' using: {command} {' '.join(args)}")
        
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        
        try:
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            
            await session.initialize()
            self.sessions[server_id] = session
            logger.info(f"Successfully connected to {server_id}")
            
            # Map tools to this server
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                self._tool_to_server[tool.name] = server_id
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_id}: {e}")
            # Do not raise error, just skip this server so others can run
            pass

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools across all connected servers."""
        all_tools = []
        for server_id, session in self.sessions.items():
            try:
                response = await session.list_tools()
                for tool in response.tools:
                    # Convert MCP tool object to a JSON schema format suitable for LLMs
                    tool_def = {
                        "name": tool.name,
                        "description": tool.description or "",
                        "input_schema": tool.inputSchema
                    }
                    all_tools.append(tool_def)
            except Exception as e:
                logger.error(f"Error listing tools for {server_id}: {e}")
        return all_tools

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call a specific tool by name."""
        server_id = self._tool_to_server.get(tool_name)
        if not server_id:
            raise ValueError(f"Unknown tool: {tool_name}. Was the server loaded?")
            
        session = self.sessions[server_id]
        logger.info(f"Calling tool '{tool_name}' on server '{server_id}'")
        
        try:
            result: CallToolResult = await session.call_tool(tool_name, arguments=arguments)
            # Combine the text content blocks from the result
            output = ""
            for content in result.content:
                if content.type == "text":
                    output += content.text + "\n"
            
            if result.isError:
                return f"Error from tool: {output}"
            return output.strip()
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return f"Exception executing tool: {e}"

    async def cleanup(self):
        """Close all connections."""
        await self.exit_stack.aclose()
        self.sessions.clear()
        self._tool_to_server.clear()


# Global synchronous instance for easy use in existing code
_global_manager = None
_loop = None

def get_manager() -> MCPManager:
    global _global_manager, _loop
    if _global_manager is None:
        _global_manager = MCPManager()
        # Initialize an event loop if none exists in this thread
        try:
            _loop = asyncio.get_event_loop()
        except RuntimeError:
            _loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop)
    return _global_manager

def start_servers():
    """Start the standard suite of MCP servers (Memory, Thinking, Research)."""
    import os
    manager = get_manager()
    loop = asyncio.get_event_loop()
    
    async def _start():
        # Server 1: Memory (uses local sqlite/json)
        await manager.connect_to_server(
            "memory",
            "npx",
            ["-y", "@modelcontextprotocol/server-memory"]
        )
        # Server 2: Sequential Thinking
        await manager.connect_to_server(
            "sequential-thinking",
            "npx",
            ["-y", "@modelcontextprotocol/server-sequential-thinking"]
        )
        
        # Server 3: Playwright (Browser Automation)
        await manager.connect_to_server(
            "playwright",
            "npx",
            ["-y", "@playwright/mcp"]
        )
        
        # Server 4: SQLite (Database Access)
        # Using uvx as python mcp-server-sqlite is the standard Python implementation
        await manager.connect_to_server(
            "sqlite",
            "uvx",
            ["mcp-server-sqlite", "--db-path", "jobs.db"]
        )
        
        # Server 5: GitHub (Repo Analysis)
        # Only launch if token is provided
        env = os.environ.copy()
        if env.get("GITHUB_PERSONAL_ACCESS_TOKEN"):
            await manager.connect_to_server(
                "github",
                "npx",
                ["-y", "@modelcontextprotocol/server-github"],
                env=env
            )
        else:
            logger.info("Skipping GitHub MCP: GITHUB_PERSONAL_ACCESS_TOKEN not set.")
            
        # Server 6: Brave Search (Web Research)
        # Only launch if API key is provided
        if env.get("BRAVE_API_KEY"):
            await manager.connect_to_server(
                "brave-search",
                "npx",
                ["-y", "@modelcontextprotocol/server-brave-search"],
                env=env
            )
        else:
            logger.info("Skipping Brave Search MCP: BRAVE_API_KEY not set.")
            
        # Server 7: Sub-Agents
        env_subagents = os.environ.copy()
        # Set a default AGENTS_DIR to point to our agents folder if not provided
        if "AGENTS_DIR" not in env_subagents:
            env_subagents["AGENTS_DIR"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents"))
            
        await manager.connect_to_server(
            "sub-agents",
            "npx",
            ["-y", "sub-agents-mcp"],
            env=env_subagents
        )
        
        # Server 8: Deep Research
        if env.get("TAVILY_API_KEY"):
            await manager.connect_to_server(
                "deep-research",
                "npx",
                ["-y", "mcp-deep-research@latest"],
                env=env
            )
        else:
            logger.info("Skipping Deep Research MCP: TAVILY_API_KEY not set.")
            
        # Server 9: Firecrawl (Stealth Scraping)
        if env.get("FIRECRAWL_API_KEY"):
            await manager.connect_to_server(
                "firecrawl",
                "npx",
                ["-y", "@mendable/firecrawl-mcp-server"],
                env=env
            )
        else:
            logger.info("Skipping Firecrawl MCP: FIRECRAWL_API_KEY not set.")
        
    loop.run_until_complete(_start())

def get_available_tools() -> List[Dict[str, Any]]:
    """Synchronous wrapper to get tools."""
    manager = get_manager()
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(manager.list_tools())

def call_tool(tool_name: str, arguments: dict) -> str:
    """Synchronous wrapper to call a tool."""
    manager = get_manager()
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(manager.call_tool(tool_name, arguments))

