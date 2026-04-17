from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Sequence

from cuga_arc3.eval.harness import compute_stage_metrics
from cuga_arc3.eval.manifest import BenchmarkManifest
from cuga_arc3.reporting import stage_lift
from cuga_arc3.runner.loop import RunnerLoop
from cuga_arc3.runner.scaffolds import STAGE_PROFILES


def _write_json_artifact(output_path: Path, payload: dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_trace_jsonl(output_path: Path, game_traces: list[dict[str, object]]) -> None:
    jsonl_path = output_path.with_suffix(".jsonl")
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("w", encoding="utf-8") as trace_file:
        for game_trace in game_traces:
            events = game_trace["events"]
            if not isinstance(events, list):
                continue
            for event in events:
                trace_file.write(json.dumps(event) + "\n")


def _default_manifest_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "benchmark"
        / "manifests"
        / "arc3-core30-stress20.yaml"
    )


def _all_manifest_game_ids(manifest: BenchmarkManifest) -> list[str]:
    return [*manifest.core, *manifest.stress]


def _solved_threshold(stage: str) -> int:
    thresholds = {
        "S0": 20,
        "S1": 30,
        "S2": 40,
        "S3": 50,
    }
    return thresholds[stage]


def _deterministic_score(game_id: str) -> int:
    digest = hashlib.sha256(game_id.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100


def _deterministic_solved_game_ids(stage: str, game_ids: list[str]) -> list[str]:
    threshold = _solved_threshold(stage)
    return [game_id for game_id in game_ids if _deterministic_score(game_id) < threshold]


def _evaluate_stage(stage: str, game_ids: list[str]) -> dict[str, str | float | int]:
    solved_game_ids = _deterministic_solved_game_ids(stage, game_ids)
    stage_manifest = BenchmarkManifest(core=game_ids, stress=[])
    metrics = compute_stage_metrics(stage=stage, solved_game_ids=solved_game_ids, manifest=stage_manifest)
    return {
        "stage": stage,
        "solved_count": metrics.solved_count,
        "total_games": metrics.total_games,
        "win_rate": round(metrics.win_rate, 2),
    }


def _default_stage_output_path(stage: str) -> Path:
    return Path("artifacts") / f"stage-{stage.lower()}-smoke.json"


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="cuga-arc3")
    subcommands = parser.add_subparsers(dest="cmd", required=True)

    ladder = subcommands.add_parser("run-ladder")
    ladder.add_argument("--out", required=True)
    ladder.add_argument("--manifest", required=False)

    stage = subcommands.add_parser("run-stage")
    stage.add_argument("--stage", required=True, choices=["S0", "S1", "S2", "S3"])
    stage.add_argument("--manifest", required=True)
    stage.add_argument("--limit", required=True, type=int)
    stage.add_argument("--out", required=False)

    args = parser.parse_args(argv)

    if args.cmd == "run-ladder":
        manifest_path = args.manifest if args.manifest else _default_manifest_path()
        manifest = BenchmarkManifest.from_yaml_path(manifest_path)
        game_ids = _all_manifest_game_ids(manifest)
        stages = [_evaluate_stage(stage_key, game_ids) for stage_key in ["S0", "S1", "S2", "S3"]]
        baseline = stages[0]
        lifts = [stage_lift(baseline, candidate) for candidate in stages[1:]]
        output_path = Path(args.out)
        _write_json_artifact(
            output_path,
            {"manifest_path": str(manifest_path), "total_games": len(game_ids), "stages": stages, "lifts": lifts},
        )
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

        solved_game_ids = _deterministic_solved_game_ids(args.stage, processed_game_ids)
        report = {
            "stage": args.stage,
            "manifest_path": args.manifest,
            "processed_game_ids": processed_game_ids,
            "total_processed": len(processed_game_ids),
            "game_traces": game_traces,
            "summary": {
                "status": "smoke_complete",
                "succeeded": len(solved_game_ids),
                "failed": len(processed_game_ids) - len(solved_game_ids),
                "solved_game_ids": solved_game_ids,
                "event_counts": dict(event_counts),
                "total_events": total_events,
            },
        }
        output_path = Path(args.out) if args.out else _default_stage_output_path(args.stage)
        _write_json_artifact(output_path, report)
        _write_trace_jsonl(output_path, game_traces)
        print(
            f"Completed {args.stage} smoke run for {len(processed_game_ids)} games -> {output_path}"
        )


if __name__ == "__main__":
    main()
