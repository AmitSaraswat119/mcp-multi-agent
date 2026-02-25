"""FastAPI app with WebSocket endpoint and MCP lifecycle management."""
import json
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from agent.mcp_client import MCPManager
from agent.orchestrator import AgentOrchestrator
from app.models import ErrorMessage


# Global MCP manager instance
mcp_manager: MCPManager = None
orchestrator: AgentOrchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect MCP servers on startup, disconnect on shutdown."""
    global mcp_manager, orchestrator
    mcp_manager = MCPManager()
    await mcp_manager.connect()
    orchestrator = AgentOrchestrator(mcp_manager)
    print(f"MCP connected: {len(mcp_manager.tools)} tools available")
    for tool in mcp_manager.tools:
        print(f"  - {tool['name']}: {tool['description'][:60]}")
    yield
    await mcp_manager.disconnect()
    print("MCP disconnected")


app = FastAPI(title="MCP Multi-Agent Demo", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint returning available tools."""
    tools = mcp_manager.tools if mcp_manager else []
    return {
        "status": "ok",
        "tools_count": len(tools),
        "tools": [t["name"] for t in tools],
    }


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for chat with real-time tool activity streaming."""
    await websocket.accept()
    conversation_history: list[dict] = []

    async def send_event(event: dict[str, Any]):
        """Send a JSON event to the frontend."""
        await websocket.send_text(json.dumps(event))

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await send_event(ErrorMessage(content="Invalid JSON").model_dump())
                continue

            if data.get("type") != "user_message":
                await send_event(
                    ErrorMessage(content=f"Unknown message type: {data.get('type')}").model_dump()
                )
                continue

            user_content = data.get("content", "").strip()
            if not user_content:
                await send_event(ErrorMessage(content="Empty message").model_dump())
                continue

            try:
                await orchestrator.run(
                    user_message=user_content,
                    conversation_history=conversation_history,
                    on_event=send_event,
                )
            except Exception as e:
                await send_event(ErrorMessage(content=f"Agent error: {str(e)}").model_dump())

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await send_event(ErrorMessage(content=f"Connection error: {str(e)}").model_dump())
        except Exception:
            pass
