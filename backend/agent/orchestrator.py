"""AgentOrchestrator: core agent loop — OpenAI GPT-4o ↔ MCP tool calls."""
import json
import os
from typing import Any, Callable, Awaitable

from openai import AsyncOpenAI

from .mcp_client import MCPManager
from .tool_registry import mcp_tools_to_openai_tools

# System prompt for the agent
SYSTEM_PROMPT = """You are a helpful AI assistant with access to three powerful tool sets:

1. **GitHub tools** (github_*): Explore repositories, read files, create issues.
2. **Web Search tools** (web_search, get_answer): Search the web and get direct answers.
3. **Filesystem tools** (fs_*): List, read, and write files in a sandboxed directory.

When a task requires multiple tools, chain them together — for example: search the web to find a repo, use GitHub to read its README, then save a summary to the filesystem.

Always be concise and helpful. If a tool call fails, explain the error and try an alternative approach."""

EventCallback = Callable[[dict[str, Any]], Awaitable[None]]


class AgentOrchestrator:
    """Implements the recursive tool-calling loop between GPT-4o and MCP servers."""

    def __init__(self, mcp_manager: MCPManager):
        self.mcp = mcp_manager
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.openai_tools = mcp_tools_to_openai_tools(mcp_manager.tools)

    async def run(
        self,
        user_message: str,
        conversation_history: list[dict],
        on_event: EventCallback,
    ) -> str:
        """Process a user message through the agent loop.

        Args:
            user_message: The user's input message.
            conversation_history: Prior conversation messages (mutated in place).
            on_event: Async callback for streaming events to the frontend.

        Returns:
            The final assistant response text.
        """
        # Append user message to history
        conversation_history.append({"role": "user", "content": user_message})

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

        # Recursive tool-calling loop
        while True:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.openai_tools if self.openai_tools else None,
                tool_choice="auto" if self.openai_tools else None,
            )

            choice = response.choices[0]
            message = choice.message

            # Add assistant response to messages
            messages.append(message.model_dump(exclude_none=True))

            if choice.finish_reason == "tool_calls" and message.tool_calls:
                # Execute all tool calls
                tool_results = []
                for tc in message.tool_calls:
                    tool_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {}

                    # Emit tool_start event
                    await on_event({
                        "type": "tool_start",
                        "tool": tool_name,
                        "args": args,
                        "call_id": tc.id,
                    })

                    # Execute tool via MCP
                    try:
                        result = await self.mcp.call_tool(tool_name, args)
                        error = None
                    except Exception as e:
                        result = f"Error: {str(e)}"
                        error = str(e)

                    # Emit tool_end event
                    await on_event({
                        "type": "tool_end",
                        "tool": tool_name,
                        "call_id": tc.id,
                        "result": result[:2000],  # Truncate for sidebar display
                        "error": error,
                    })

                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

                # Feed results back into the loop
                messages.extend(tool_results)
                continue

            # Final text response
            final_text = message.content or ""

            # Append to conversation history
            conversation_history.append({"role": "assistant", "content": final_text})

            # Emit assistant message event
            await on_event({
                "type": "assistant_message",
                "content": final_text,
            })

            return final_text
