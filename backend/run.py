"""Entry point: loads .env and starts the FastAPI server with uvicorn."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from backend directory or parent
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")

import uvicorn


def main():
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
