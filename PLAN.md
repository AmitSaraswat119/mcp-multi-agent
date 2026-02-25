# MCP Multi-Agent Demo — Implementation Plan

## Context
Build a multi-tool MCP agent demo: 3 Python MCP servers (GitHub, Web Search, File System) orchestrated by a single agent using OpenAI GPT-4o, with a React chat UI showing real-time tool activity.

## Project Structure

```
/Users/amitsaraswat/MCP/
├── backend/
│   ├── pyproject.toml
│   ├── .env.example
│   ├── run.py                         # Entry point: starts FastAPI + MCP servers
│   ├── servers/
│   │   ├── __init__.py
│   │   ├── github_server.py           # MCP Server #1: list_repos, read_file, create_issue
│   │   ├── web_search_server.py       # MCP Server #2: web_search, get_answer (Tavily)
│   │   └── filesystem_server.py       # MCP Server #3: list_files, read_file, write_file
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── mcp_client.py             # Manages stdio connections to all 3 servers
│   │   ├── tool_registry.py          # MCP tools → OpenAI function schema converter
│   │   └── orchestrator.py           # Core agent loop: OpenAI ↔ MCP tool calls
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI + WebSocket endpoint
│   │   └── models.py                 # Pydantic event models
│   └── sample_files/                 # Sandbox for filesystem MCP
│       ├── example.txt
│       └── notes.md
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx                   # Layout: chat + sidebar
│       ├── App.css                   # Dark theme styles
│       ├── components/
│       │   ├── ChatWindow.jsx        # Message list + input
│       │   ├── ChatMessage.jsx       # User/assistant bubble
│       │   ├── ToolSidebar.jsx       # Tool activity sidebar
│       │   └── ToolCard.jsx          # Single tool invocation card
│       ├── hooks/
│       │   └── useWebSocket.js       # WebSocket + state management
│       └── styles/
│           ├── ChatWindow.css
│           ├── ToolSidebar.css
│           └── ToolCard.css
└── .gitignore
```

## Implementation Steps

### Step 1: Project scaffolding
- Create the full directory structure
- Write `pyproject.toml` with deps: `mcp>=1.7`, `fastapi`, `uvicorn`, `openai`, `PyGithub`, `tavily-python`, `python-dotenv`
- Write `.env.example` (OPENAI_API_KEY, GITHUB_TOKEN, TAVILY_API_KEY)
- Write `.gitignore`
- Scaffold frontend with `package.json` (react 19, vite 6) and `vite.config.js` (proxy `/ws` to backend)

### Step 2: MCP Servers (3 files)
- **github_server.py** — FastMCP server with 3 tools: `list_repos(username)`, `read_file(repo_full_name, file_path, branch)`, `create_issue(repo_full_name, title, body)`. Uses PyGithub.
- **web_search_server.py** — FastMCP server with 2 tools: `web_search(query, max_results)`, `get_answer(query)`. Uses Tavily client.
- **filesystem_server.py** — FastMCP server with 3 tools: `list_files(directory)`, `read_file(file_path)`, `write_file(file_path, content)`. Sandboxed to `sample_files/` with path traversal protection.
- All use `mcp.run(transport="stdio")` entry point.

### Step 3: Agent layer (3 files)
- **mcp_client.py** — `MCPManager` class: spawns all 3 servers as stdio subprocesses, discovers tools, prefixes tool names by server (`github_`, `fs_`) to avoid collisions, routes `call_tool()` to correct session.
- **tool_registry.py** — Pure function `mcp_tools_to_openai_tools()` converting MCP tool metadata to OpenAI function-calling format.
- **orchestrator.py** — `AgentOrchestrator` class: implements the recursive tool-calling loop. Calls GPT-4o → if tool_calls returned → execute via MCP → feed results back → repeat until final text response. Emits `tool_start`, `tool_end`, `assistant_message` events via callback.

### Step 4: FastAPI app (3 files)
- **models.py** — Pydantic models for WebSocket events (ToolStartEvent, ToolEndEvent, AssistantMessage, ErrorMessage)
- **main.py** — FastAPI with lifespan (connect MCP on startup, disconnect on shutdown), WebSocket endpoint at `/ws/chat`, CORS for localhost:5173, `/health` REST endpoint
- **run.py** — Entry point: loads `.env`, runs uvicorn

### Step 5: React frontend
- **useWebSocket.js** — Custom hook: manages WS connection, parses incoming events, maintains `messages[]` and `toolEvents[]` state
- **App.jsx** — CSS Grid layout: 70% chat panel + 30% tool sidebar, connection status indicator
- **ChatWindow.jsx** — Scrollable message list + input form, loading indicator
- **ChatMessage.jsx** — User (right, blue) / assistant (left, gray) bubbles
- **ToolSidebar.jsx** — Reverse-chronological tool event list with color-coded server labels
- **ToolCard.jsx** — Expandable card: tool name, args preview, spinner while running, collapsible result
- **CSS** — Dark theme with CSS variables. Server colors: purple (GitHub), blue (Search), amber (Filesystem)

### Step 6: Sample files + final wiring
- Create `sample_files/example.txt` and `sample_files/notes.md` with demo content
- Write `index.html` for Vite

## 8 MCP Tools Exposed to GPT-4o

| Tool | Server | Parameters |
|------|--------|------------|
| `github_list_repos` | GitHub | `username: str` |
| `github_read_file` | GitHub | `repo_full_name, file_path, branch="main"` |
| `github_create_issue` | GitHub | `repo_full_name, title, body=""` |
| `web_search` | Search | `query, max_results=5` |
| `get_answer` | Search | `query` |
| `fs_list_files` | Filesystem | `directory=""` |
| `fs_read_file` | Filesystem | `file_path` |
| `fs_write_file` | Filesystem | `file_path, content` |

## Multi-Tool Chaining (the star feature)

The orchestrator implements a recursive tool-calling loop:

1. Send user message + tool definitions to GPT-4o
2. If GPT-4o returns `tool_calls` → execute each via MCP → feed results back → repeat
3. If GPT-4o returns plain text → done

**Example chain:** "Find a popular Python repo, read its README, save a summary"
- `web_search` → finds repo → `github_read_file` → gets README → `fs_write_file` → saves summary
- 3 tool calls across 3 different MCP servers in one conversation turn

## Architecture Details

### Transport
- **stdio** — each MCP server runs as a subprocess spawned by the agent. Simple, no port management.

### WebSocket Protocol
Frontend ↔ Backend events:
```json
// Frontend → Backend
{"type": "user_message", "content": "..."}

// Backend → Frontend
{"type": "tool_start", "tool": "web_search", "args": {...}, "call_id": "..."}
{"type": "tool_end", "tool": "web_search", "call_id": "...", "result": "..."}
{"type": "assistant_message", "content": "..."}
{"type": "error", "content": "..."}
```

### Tool Name Collision Resolution
Both GitHub and Filesystem servers have `read_file`. Solved by prefixing in `MCPManager`:
- GitHub's `read_file` → `github_read_file`
- Filesystem's `read_file` → `fs_read_file`

Prefixing happens in the client layer only — servers stay clean and independently reusable.

### Frontend Dark Theme
```css
--bg-primary: #0f1117;
--bg-secondary: #1a1d27;
--bg-card: #232734;
--text-primary: #e2e8f0;
--accent-github: #8b5cf6;    /* purple */
--accent-search: #3b82f6;    /* blue */
--accent-filesystem: #f59e0b; /* amber */
```

## Verification
1. `cd backend && pip install -e . && python run.py` — backend starts, `/health` returns 8 tools
2. `cd frontend && npm install && npm run dev` — frontend at localhost:5173
3. Test: "List repos for octocat" → sidebar shows `github_list_repos`
4. Test: "Search the web for latest AI news" → sidebar shows `web_search`
5. Test: "Write a summary to notes.md" → sidebar shows `fs_write_file`
6. Test multi-chain: "Find a popular Python repo on GitHub, read its README, and save a summary locally" → 3+ tool calls across all servers

## Prerequisites
- Python 3.10+ (mcp SDK requirement)
- Node.js 20+
- API keys: `OPENAI_API_KEY`, `GITHUB_TOKEN`, `TAVILY_API_KEY`
