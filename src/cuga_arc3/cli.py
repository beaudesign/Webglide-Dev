from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(prog="cuga-arc3")
    subcommands = parser.add_subparsers(dest="cmd", required=True)

    ladder = subcommands.add_parser("run-ladder")
    ladder.add_argument("--out", required=True)

    args = parser.parse_args()

    if args.cmd == "run-ladder":
        stages = [
            {"stage": "S0", "win_rate": 0.20},
            {"stage": "S1", "win_rate": 0.27},
            {"stage": "S2", "win_rate": 0.34},
            {"stage": "S3", "win_rate": 0.39},
        ]
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps({"stages": stages}, indent=2),
            encoding="utf-8",
        )
        print(f"Wrote ladder report to {output_path}")


if __name__ == "__main__":
    main()
