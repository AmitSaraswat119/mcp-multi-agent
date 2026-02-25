"""Pydantic models for WebSocket events."""
from typing import Any, Literal, Optional
from pydantic import BaseModel


class UserMessage(BaseModel):
    type: Literal["user_message"] = "user_message"
    content: str


class ToolStartEvent(BaseModel):
    type: Literal["tool_start"] = "tool_start"
    tool: str
    args: dict[str, Any]
    call_id: str


class ToolEndEvent(BaseModel):
    type: Literal["tool_end"] = "tool_end"
    tool: str
    call_id: str
    result: str
    error: Optional[str] = None


class AssistantMessage(BaseModel):
    type: Literal["assistant_message"] = "assistant_message"
    content: str


class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    content: str
