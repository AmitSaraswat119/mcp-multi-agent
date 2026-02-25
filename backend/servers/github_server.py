"""MCP Server #1: GitHub — list_repos, read_file, create_issue."""
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from mcp.server.fastmcp import FastMCP
from github import Github, GithubException

mcp = FastMCP("github")


def _get_client() -> Github:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN environment variable not set")
    return Github(token)


@mcp.tool()
def list_repos(username: str) -> list[dict]:
    """List public repositories for a GitHub user.

    Args:
        username: GitHub username to list repositories for.

    Returns:
        List of dicts with name, description, stars, language, url.
    """
    g = _get_client()
    try:
        user = g.get_user(username)
        repos = []
        for repo in user.get_repos():
            repos.append({
                "name": repo.full_name,
                "description": repo.description or "",
                "stars": repo.stargazers_count,
                "language": repo.language or "",
                "url": repo.html_url,
            })
        return sorted(repos, key=lambda r: r["stars"], reverse=True)
    except GithubException as e:
        raise RuntimeError(f"GitHub API error: {e.data.get('message', str(e))}")


@mcp.tool()
def read_file(repo_full_name: str, file_path: str, branch: str = "main") -> str:
    """Read the content of a file from a GitHub repository.

    Args:
        repo_full_name: Repository in 'owner/repo' format.
        file_path: Path to the file within the repository.
        branch: Branch name (default: main).

    Returns:
        File content as a string.
    """
    g = _get_client()
    try:
        repo = g.get_repo(repo_full_name)
        contents = repo.get_contents(file_path, ref=branch)
        if isinstance(contents, list):
            raise RuntimeError(f"'{file_path}' is a directory, not a file")
        return contents.decoded_content.decode("utf-8")
    except GithubException as e:
        # Try master branch if main fails
        if branch == "main":
            try:
                repo = g.get_repo(repo_full_name)
                contents = repo.get_contents(file_path, ref="master")
                if isinstance(contents, list):
                    raise RuntimeError(f"'{file_path}' is a directory, not a file")
                return contents.decoded_content.decode("utf-8")
            except GithubException:
                pass
        raise RuntimeError(f"GitHub API error: {e.data.get('message', str(e))}")


@mcp.tool()
def create_issue(repo_full_name: str, title: str, body: str = "") -> dict:
    """Create a new issue in a GitHub repository.

    Args:
        repo_full_name: Repository in 'owner/repo' format.
        title: Issue title.
        body: Issue body/description (optional).

    Returns:
        Dict with issue number, title, url.
    """
    g = _get_client()
    try:
        repo = g.get_repo(repo_full_name)
        issue = repo.create_issue(title=title, body=body)
        return {
            "number": issue.number,
            "title": issue.title,
            "url": issue.html_url,
            "state": issue.state,
        }
    except GithubException as e:
        raise RuntimeError(f"GitHub API error: {e.data.get('message', str(e))}")


if __name__ == "__main__":
    mcp.run(transport="stdio")
