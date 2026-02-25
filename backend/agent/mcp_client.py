"""MCPManager: spawns all 3 MCP servers as stdio subprocesses and routes tool calls."""
import asyncio
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# Server definitions: (prefix, script_path)
SERVERS = [
    ("github", Path(__file__).parent.parent / "servers" / "github_server.py"),
    ("web", Path(__file__).parent.parent / "servers" / "web_search_server.py"),
    ("fs", Path(__file__).parent.parent / "servers" / "filesystem_server.py"),
]

# Tool name prefix mapping from plan:
# github_server tools: list_repos, read_file, create_issue → github_list_repos, github_read_file, github_create_issue
# web_search_server tools: web_search, get_answer → web_search, get_answer (no prefix needed, but we prefix anyway)
# filesystem_server tools: list_files, read_file, write_file → fs_list_files, fs_read_file, fs_write_file
SERVER_PREFIXES = {
    "github": "github",
    "web": "web",
    "fs": "fs",
}

# Override specific tool names to match the plan exactly
TOOL_NAME_OVERRIDES = {
    "web_web_search": "web_search",
    "web_get_answer": "get_answer",
}


class MCPManager:
    """Manages stdio connections to all MCP servers."""

    def __init__(self):
        self._sessions: dict[str, ClientSession] = {}
        self._tool_to_server: dict[str, str] = {}  # exposed_name → server_prefix
        self._tool_to_real: dict[str, str] = {}    # exposed_name → real tool name on server
        self._tools_list: list[dict] = []           # list of MCP tool metadata dicts
        self._context_managers = []
        self._exit_stacks = []

    async def connect(self):
        """Spawn all MCP server subprocesses and discover their tools."""
        for prefix, script_path in SERVERS:
            params = StdioServerParameters(
                command=sys.executable,
                args=[str(script_path)],
                env=None,
            )
            cm = stdio_client(params)
            read, write = await cm.__aenter__()
            self._context_managers.append(cm)

            session = ClientSession(read, write)
            await session.__aenter__()
            self._exit_stacks.append(session)

            await session.initialize()
            self._sessions[prefix] = session

            # Discover tools
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                raw_name = f"{prefix}_{tool.name}"
                exposed_name = TOOL_NAME_OVERRIDES.get(raw_name, raw_name)
                self._tool_to_server[exposed_name] = prefix
                self._tool_to_real[exposed_name] = tool.name
                self._tools_list.append({
                    "name": exposed_name,
                    "description": tool.description or "",
                    "inputSchema": tool.inputSchema,
                })

    async def disconnect(self):
        """Close all sessions and subprocesses."""
        for session in reversed(self._exit_stacks):
            try:
                await session.__aexit__(None, None, None)
            except Exception:
                pass
        for cm in reversed(self._context_managers):
            try:
                await cm.__aexit__(None, None, None)
            except Exception:
                pass

    @property
    def tools(self) -> list[dict]:
        """Return list of all discovered MCP tool metadata."""
        return self._tools_list

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Route a tool call to the correct server and return the result as a string."""
        if tool_name not in self._tool_to_server:
            raise ValueError(f"Unknown tool: {tool_name}")

        prefix = self._tool_to_server[tool_name]
        real_name = self._tool_to_real[tool_name]
        session = self._sessions[prefix]

        result = await session.call_tool(real_name, arguments=arguments)

        # Extract text content from result
        if result.content:
            parts = []
            for item in result.content:
                if hasattr(item, "text"):
                    parts.append(item.text)
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        return ""
