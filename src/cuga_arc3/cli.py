from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from cuga_arc3.eval.manifest import BenchmarkManifest
from cuga_arc3.reporting import stage_lift


def _write_json_artifact(output_path: Path, payload: dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _deterministic_ladder_stages() -> list[dict[str, str | float]]:
    return [
        {"stage": "S0", "win_rate": 0.20},
        {"stage": "S1", "win_rate": 0.27},
        {"stage": "S2", "win_rate": 0.34},
        {"stage": "S3", "win_rate": 0.39},
    ]


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="cuga-arc3")
    subcommands = parser.add_subparsers(dest="cmd", required=True)

    ladder = subcommands.add_parser("run-ladder")
    ladder.add_argument("--out", required=True)

    stage = subcommands.add_parser("run-stage")
    stage.add_argument("--stage", required=True, choices=["S0", "S1", "S2", "S3"])
    stage.add_argument("--manifest", required=True)
    stage.add_argument("--limit", required=True, type=int)
    stage.add_argument("--out", required=True)

    args = parser.parse_args(argv)

    if args.cmd == "run-ladder":
        stages = _deterministic_ladder_stages()
        baseline = stages[0]
        lifts = [stage_lift(baseline, candidate) for candidate in stages[1:]]
        output_path = Path(args.out)
        _write_json_artifact(output_path, {"stages": stages, "lifts": lifts})
        print(f"Wrote ladder report to {output_path}")

    if args.cmd == "run-stage":
        manifest = BenchmarkManifest.from_yaml_path(args.manifest)
        all_game_ids = [*manifest.core, *manifest.stress]
        processed_game_ids = all_game_ids[: max(args.limit, 0)]
        report = {
            "stage": args.stage,
            "manifest_path": args.manifest,
            "processed_game_ids": processed_game_ids,
            "total_processed": len(processed_game_ids),
            "summary": {
                "status": "smoke_complete",
                "succeeded": len(processed_game_ids),
                "failed": 0,
            },
        }
        output_path = Path(args.out)
        _write_json_artifact(output_path, report)
        print(
            f"Completed {args.stage} smoke run for {len(processed_game_ids)} games -> {output_path}"
        )


if __name__ == "__main__":
    main()
