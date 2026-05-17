"""CLI for semipilot prompt-driven automation."""

from __future__ import annotations

import argparse
import json

from .config import load_config
from .pipeline import run_semipilot


def main() -> int:
    parser = argparse.ArgumentParser(description="Run semipilot prompt automation.")
    parser.add_argument(
        "--config",
        default="semipilot/config.json",
        help="Path to semipilot config JSON.",
    )
    args = parser.parse_args()
    config = load_config(args.config)
    summary = run_semipilot(config)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

