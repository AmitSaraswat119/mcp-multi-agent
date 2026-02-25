# ⚡ MCP Multi-Agent Demo

A full-stack demo of the **Model Context Protocol (MCP)** — three Python MCP servers orchestrated by GPT-4o, with a React chat UI showing real-time tool activity.

![Architecture](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square) ![Frontend](https://img.shields.io/badge/Frontend-React_19-61dafb?style=flat-square) ![AI](https://img.shields.io/badge/AI-GPT--4o-412991?style=flat-square) ![Protocol](https://img.shields.io/badge/Protocol-MCP_1.7-orange?style=flat-square)

---

## What It Does

You type a message in the chat. GPT-4o decides which tools to call, calls them via MCP, feeds the results back to itself, and repeats until it has a final answer. Every tool call streams to the sidebar in real time.

**Example chain:** *"Find a popular Python repo, read its README, save a summary locally"*
1. `web_search` → finds the repo
2. `github_read_file` → reads the README
3. `fs_write_file` → saves the summary

Three tool calls across three different MCP servers in one turn.

---

## Architecture

```
User
 │
 ▼
React UI (localhost:5173)
 │  WebSocket /ws/chat
 ▼
FastAPI Backend (localhost:8000)
 │
 ├─► AgentOrchestrator
 │     └─► OpenAI GPT-4o
 │           └─► tool_calls
 │
 └─► MCPManager
       ├─► github_server.py    (stdio subprocess)
       ├─► web_search_server.py (stdio subprocess)
       └─► filesystem_server.py (stdio subprocess)
```

Each MCP server runs as a **stdio subprocess** — no ports, no networking between servers.

---

## Project Structure

```
MCP/
├── backend/
│   ├── pyproject.toml
│   ├── .env.example
│   ├── run.py                      # Entry point
│   ├── servers/
│   │   ├── github_server.py        # MCP Server #1
│   │   ├── web_search_server.py    # MCP Server #2
│   │   └── filesystem_server.py   # MCP Server #3
│   ├── agent/
│   │   ├── mcp_client.py          # Spawns servers, routes tool calls
│   │   ├── tool_registry.py       # MCP → OpenAI schema converter
│   │   └── orchestrator.py        # GPT-4o ↔ MCP agent loop
│   ├── app/
│   │   ├── main.py                # FastAPI + WebSocket endpoint
│   │   └── models.py              # Pydantic event models
│   └── sample_files/              # Sandbox for filesystem tools
│       ├── example.txt
│       └── notes.md
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx                # Layout: chat + sidebar
│       ├── components/
│       │   ├── ChatWindow.jsx
│       │   ├── ChatMessage.jsx
│       │   ├── ToolSidebar.jsx
│       │   └── ToolCard.jsx
│       └── hooks/
│           └── useWebSocket.js
└── README.md
```

---

## Tools Available to GPT-4o

| Tool | Server | What It Does |
|------|--------|--------------|
| `github_list_repos` | GitHub | List public repos for a user |
| `github_read_file` | GitHub | Read a file from any GitHub repo |
| `github_create_issue` | GitHub | Create an issue in a repo |
| `web_search` | Search | Search the web (via Tavily) |
| `get_answer` | Search | Get a direct AI answer from web context |
| `fs_list_files` | Filesystem | List files in the sandbox |
| `fs_read_file` | Filesystem | Read a sandboxed file |
| `fs_write_file` | Filesystem | Write/create a sandboxed file |

---

## Prerequisites

- **Python 3.10+**
- **Node.js 20+**
- API keys:
  - `OPENAI_API_KEY` — [platform.openai.com](https://platform.openai.com/api-keys)
  - `GITHUB_TOKEN` — [github.com/settings/tokens](https://github.com/settings/tokens) (scopes: `public_repo`)
  - `TAVILY_API_KEY` — [app.tavily.com](https://app.tavily.com)

---

## Setup & Run

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd MCP
```

### 2. Backend

```bash
cd backend

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys

# Start the server
python run.py
```

Backend runs at **http://localhost:8000**. Verify with:
```bash
curl http://localhost:8000/health
# → {"status":"ok","tools_count":8,"tools":[...]}
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:5173**.

---

## Usage

Open **http://localhost:5173** in your browser and start chatting.

### Try these prompts

**Single tool:**
```
List repos for octocat
```
```
Search the web for latest AI news
```
```
List the files in my sandbox
```

**Multi-tool chain (uses all 3 servers):**
```
Search the web to find a popular Python open-source project, find its GitHub
repository, read the README, check my local files, and save a detailed summary
with key takeaways to research.md
```

Watch the **Tool Activity** sidebar — each tool call appears with a spinner while running and a result you can expand when done. Server colors: **purple** = GitHub, **blue** = Search, **amber** = Filesystem.

---

## WebSocket Protocol

```json
// Frontend → Backend
{ "type": "user_message", "content": "..." }

// Backend → Frontend
{ "type": "tool_start", "tool": "web_search", "args": {...}, "call_id": "..." }
{ "type": "tool_end",   "tool": "web_search", "call_id": "...", "result": "..." }
{ "type": "assistant_message", "content": "..." }
{ "type": "error", "content": "..." }
```

---

## Key Design Decisions

**Tool name collision handling** — both GitHub and Filesystem servers have a `read_file` tool. The `MCPManager` prefixes tool names by server (`github_read_file`, `fs_read_file`). The servers themselves stay clean and independently reusable.

**stdio transport** — each MCP server is a subprocess communicating over stdin/stdout. No port management, no service discovery, simple process lifecycle tied to the FastAPI app.

**Sandboxed filesystem** — the filesystem server resolves all paths relative to `sample_files/` and rejects path traversal attempts, so GPT-4o can only read/write within that directory.

---

## License

MIT
