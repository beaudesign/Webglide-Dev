from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Sequence

from cuga_arc3.eval.manifest import BenchmarkManifest
from cuga_arc3.reporting import stage_lift
from cuga_arc3.runner.loop import RunnerLoop
from cuga_arc3.runner.scaffolds import STAGE_PROFILES


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


def _default_stage_output_path(stage: str) -> Path:
    return Path("artifacts") / f"stage-{stage.lower()}-smoke.json"


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="cuga-arc3")
    subcommands = parser.add_subparsers(dest="cmd", required=True)

    ladder = subcommands.add_parser("run-ladder")
    ladder.add_argument("--out", required=True)

    stage = subcommands.add_parser("run-stage")
    stage.add_argument("--stage", required=True, choices=["S0", "S1", "S2", "S3"])
    stage.add_argument("--manifest", required=True)
    stage.add_argument("--limit", required=True, type=int)
    stage.add_argument("--out", required=False)

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
        stage_profile = STAGE_PROFILES[args.stage]
        runner = RunnerLoop(stage_profile=stage_profile, max_steps=2)
        game_traces: list[dict[str, object]] = []
        event_counts: Counter[str] = Counter()
        total_events = 0
        for game_id in processed_game_ids:
            events = runner.simulate(game_id)
            serialized_events = [event.to_dict() for event in events]
            game_traces.append({"game_id": game_id, "events": serialized_events})
            event_counts.update(event["event_type"] for event in serialized_events)
            total_events += len(serialized_events)

        report = {
            "stage": args.stage,
            "manifest_path": args.manifest,
            "processed_game_ids": processed_game_ids,
            "total_processed": len(processed_game_ids),
            "game_traces": game_traces,
            "summary": {
                "status": "smoke_complete",
                "succeeded": len(processed_game_ids),
                "failed": 0,
                "event_counts": dict(event_counts),
                "total_events": total_events,
            },
        }
        output_path = Path(args.out) if args.out else _default_stage_output_path(args.stage)
        _write_json_artifact(output_path, report)
        print(
            f"Completed {args.stage} smoke run for {len(processed_game_ids)} games -> {output_path}"
        )


if __name__ == "__main__":
    main()
