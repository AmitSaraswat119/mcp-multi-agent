"""Convert MCP tool metadata to OpenAI function-calling schema format."""
from typing import Any


def mcp_tools_to_openai_tools(mcp_tools: list[dict]) -> list[dict[str, Any]]:
    """Convert a list of MCP tool metadata dicts to OpenAI function-calling format.

    Args:
        mcp_tools: List of dicts with keys: name, description, inputSchema.

    Returns:
        List of OpenAI tool dicts in the function-calling format.
    """
    openai_tools = []
    for tool in mcp_tools:
        input_schema = tool.get("inputSchema", {})
        # Ensure the schema is a valid JSON Schema object
        if not isinstance(input_schema, dict):
            input_schema = {"type": "object", "properties": {}}

        # OpenAI requires type=object at the root
        if input_schema.get("type") != "object":
            input_schema = {
                "type": "object",
                "properties": input_schema,
            }

        # Remove any keys OpenAI doesn't support
        cleaned_schema = {
            "type": "object",
            "properties": input_schema.get("properties", {}),
        }
        if "required" in input_schema:
            cleaned_schema["required"] = input_schema["required"]

        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": cleaned_schema,
            },
        })
    return openai_tools
