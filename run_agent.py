"""CLI entrypoint for fully automated Lead Finder pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.orchestrator import run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Lead Finder AI pipeline.")
    parser.add_argument(
        "--config",
        default="src/config/app.config.json",
        help="Path to runtime JSON config file.",
    )
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config not found at {config_path}. Copy src/config/app.config.example.json to this path and fill values."
        )

    summary = run_pipeline(config_path=config_path)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

