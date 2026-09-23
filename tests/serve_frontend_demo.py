from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from src.api import create_app
from src.core.settings import Settings
from src.workflow import PrismKEService


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the isolated PrismKE browser fixture")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    settings = Settings(
        _env_file=None,
        runtime_dir=args.runtime,
        embedding_provider="mock",
        graph_store="json",
    )
    app = create_app(settings, PrismKEService(settings))
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
