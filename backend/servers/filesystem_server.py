"""MCP Server #3: Filesystem — list_files, read_file, write_file (sandboxed)."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("filesystem")

# Sandbox root: only allow access within sample_files/
SANDBOX_ROOT = (Path(__file__).parent.parent / "sample_files").resolve()


def _safe_path(relative_path: str) -> Path:
    """Resolve path and ensure it stays within the sandbox."""
    if not relative_path or relative_path in (".", ""):
        return SANDBOX_ROOT
    target = (SANDBOX_ROOT / relative_path).resolve()
    if not str(target).startswith(str(SANDBOX_ROOT)):
        raise PermissionError(
            f"Path traversal detected. Access restricted to {SANDBOX_ROOT}"
        )
    return target


@mcp.tool()
def list_files(directory: str = "") -> list[dict]:
    """List files and directories in the sandbox.

    Args:
        directory: Relative path within the sandbox (default: root of sandbox).

    Returns:
        List of dicts with name, type (file/directory), size.
    """
    target = _safe_path(directory)
    if not target.exists():
        raise FileNotFoundError(f"Directory '{directory}' does not exist in sandbox")
    if not target.is_dir():
        raise NotADirectoryError(f"'{directory}' is not a directory")

    items = []
    for entry in sorted(target.iterdir()):
        rel_path = entry.relative_to(SANDBOX_ROOT)
        items.append({
            "name": str(rel_path),
            "type": "directory" if entry.is_dir() else "file",
            "size": entry.stat().st_size if entry.is_file() else None,
        })
    return items


@mcp.tool()
def read_file(file_path: str) -> str:
    """Read the content of a file from the sandbox.

    Args:
        file_path: Relative path to the file within the sandbox.

    Returns:
        File content as a string.
    """
    target = _safe_path(file_path)
    if not target.exists():
        raise FileNotFoundError(f"File '{file_path}' does not exist in sandbox")
    if not target.is_file():
        raise IsADirectoryError(f"'{file_path}' is a directory, not a file")
    return target.read_text(encoding="utf-8")


@mcp.tool()
def write_file(file_path: str, content: str) -> dict:
    """Write content to a file in the sandbox (creates or overwrites).

    Args:
        file_path: Relative path to the file within the sandbox.
        content: Text content to write to the file.

    Returns:
        Dict with path, bytes_written, created (bool).
    """
    target = _safe_path(file_path)
    existed = target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {
        "path": str(target.relative_to(SANDBOX_ROOT)),
        "bytes_written": len(content.encode("utf-8")),
        "created": not existed,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
