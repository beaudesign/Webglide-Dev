from __future__ import annotations

import argparse
import asyncio
import hashlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from cuga_arc3.arc_adapter.client import ArcClient
from cuga_arc3.artifacts.schema import RunArtifact
from cuga_arc3.artifacts.writer import ArtifactWriter
from cuga_arc3.config import Settings
from cuga_arc3.eval.harness import compute_live_stage_metrics, compute_stage_metrics
from cuga_arc3.eval.manifest import BenchmarkManifest
from cuga_arc3.prompts import resolve_master_prompt
from cuga_arc3.reporting import stage_lift
from cuga_arc3.runner.loop import RunnerLoop
from cuga_arc3.runner.scaffolds import STAGE_PROFILES
from cuga_arc3.watch_http import run_watch_server


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _extract_card_id(scorecard_payload: object) -> str:
    if isinstance(scorecard_payload, dict):
        for key in ("card_id", "id", "guid"):
            value = scorecard_payload.get(key)
            if isinstance(value, str) and value:
                return value
    raise ValueError("open_scorecard response must include card_id, id, or guid")


def _trace_has_solved_episode(serialized_events: list[dict[str, object]]) -> bool:
    for event in reversed(serialized_events):
        if event.get("event_type") != "episode_end":
            continue
        payload = event.get("payload")
        if isinstance(payload, dict):
            return payload.get("stop_reason") == "solved"
    return False


async def _run_live_ladder_command(
    args: argparse.Namespace,
    manifest: BenchmarkManifest,
    manifest_path: str | Path,
    game_ids: list[str],
) -> None:
    settings = Settings.from_env_optional()
    if settings is None:
        print("ARC_API_KEY not set — --live requires ARC_API_KEY")
        raise SystemExit(1)

    client = ArcClient(base_url=settings.arc_base_url, api_key=settings.arc_api_key)
    stages: list[dict[str, object]] = []
    all_game_traces: list[dict[str, object]] = []
    master_prompt = resolve_master_prompt(
        inline=args.master_prompt,
        file_path=args.master_prompt_file,
        manifest_master_prompt=manifest.master_prompt,
    )

    for stage_key in ["S0", "S1", "S2", "S3"]:
        scorecard_payload = await client.open_scorecard(
            {
                "stage": stage_key,
                "manifest_path": str(manifest_path),
                "total_games": len(game_ids),
            }
        )
        card_id = _extract_card_id(scorecard_payload)

        runner = RunnerLoop(
            stage_profile=STAGE_PROFILES[stage_key],
            max_steps=settings.max_steps_per_game,
            master_prompt=master_prompt,
        )
        stage_game_traces: list[dict[str, object]] = []
        for game_id in game_ids:
            events = await runner.run(game_id=game_id, client=client, card_id=card_id)
            serialized_events = [event.to_dict() for event in events]
            stage_game_traces.append({"game_id": game_id, "events": serialized_events})

        scorecard_result = await client.close_scorecard(card_id)
        metrics = compute_live_stage_metrics(
            stage=stage_key,
            game_traces=stage_game_traces,
            manifest=manifest,
        )
        stage_result = {
            "stage": stage_key,
            "solved_count": metrics.solved_count,
            "total_games": metrics.total_games,
            "win_rate": round(metrics.win_rate, 2),
            "card_id": card_id,
            "scorecard_result": scorecard_result,
        }
        stages.append(stage_result)
        all_game_traces.extend(stage_game_traces)
        print(
            f"{stage_key} win_rate={stage_result['win_rate']:.2f} "
            f"({metrics.solved_count}/{metrics.total_games})"
        )

    baseline = stages[0]
    lifts = [stage_lift(baseline, candidate) for candidate in stages[1:]]
    output_path = Path(args.out)
    artifact = RunArtifact(
        run_id=output_path.stem,
        stage="ladder",
        manifest_path=str(manifest_path),
        total_games=len(game_ids),
        created_at=_utc_timestamp(),
        stages=stages,
        lifts=lifts,
        game_traces=all_game_traces,
    )
    writer = ArtifactWriter(output_path.parent)
    json_path, _ = writer.write(artifact)
    print(f"Wrote ladder report to {json_path}")


async def _run_stage_command(args: argparse.Namespace) -> None:
    try:
        manifest = BenchmarkManifest.from_yaml_path(args.manifest)
    except ValueError:
        manifest = BenchmarkManifest.from_yaml_path_flexible(args.manifest)
    all_game_ids = [*manifest.core, *manifest.stress]
    processed_game_ids = all_game_ids[: max(args.limit, 0)]
    stage_profile = STAGE_PROFILES[args.stage]
    settings = Settings.from_env_optional()
    use_live_execution = settings is not None
    master_prompt = resolve_master_prompt(
        inline=args.master_prompt,
        file_path=args.master_prompt_file,
        manifest_master_prompt=manifest.master_prompt,
    )
    max_steps = (
        args.max_steps
        if args.max_steps is not None
        else (settings.max_steps_per_game if settings is not None else 2)
    )
    runner = RunnerLoop(
        stage_profile=stage_profile,
        max_steps=max_steps,
        master_prompt=master_prompt,
    )

    game_traces: list[dict[str, object]] = []
    event_counts: Counter[str] = Counter()
    total_events = 0
    solved_game_ids_live: list[str] = []

    if use_live_execution and settings is not None:
        async with ArcClient(
            base_url=settings.arc_base_url, api_key=settings.arc_api_key
        ) as client:
            scorecard_payload = await client.open_scorecard(
                {
                    "stage": args.stage,
                    "manifest_path": args.manifest,
                    "total_games": len(processed_game_ids),
                    "created_at": _utc_timestamp(),
                }
            )
            card_id = _extract_card_id(scorecard_payload)
            for game_id in processed_game_ids:
                events = await runner.run(game_id=game_id, client=client, card_id=card_id)
                serialized_events = [event.to_dict() for event in events]
                game_traces.append({"game_id": game_id, "events": serialized_events})
                event_counts.update(event["event_type"] for event in serialized_events)
                total_events += len(serialized_events)
                if _trace_has_solved_episode(serialized_events):
                    solved_game_ids_live.append(game_id)
    else:
        print("ARC_API_KEY not set — running in simulation mode")
        for game_id in processed_game_ids:
            events = runner.simulate(game_id)
            serialized_events = [event.to_dict() for event in events]
            game_traces.append({"game_id": game_id, "events": serialized_events})
            event_counts.update(event["event_type"] for event in serialized_events)
            total_events += len(serialized_events)

    solved_game_ids = (
        solved_game_ids_live
        if use_live_execution
        else _deterministic_solved_game_ids(args.stage, processed_game_ids)
    )
    summary: dict[str, object] = {
        "status": "smoke_complete",
        "succeeded": len(solved_game_ids),
        "failed": len(processed_game_ids) - len(solved_game_ids),
        "solved_game_ids": solved_game_ids,
        "event_counts": dict(event_counts),
        "total_events": total_events,
        "max_steps_per_episode": max_steps,
    }
    if master_prompt:
        summary["master_prompt"] = master_prompt
    report = {
        "stage": args.stage,
        "manifest_path": args.manifest,
        "processed_game_ids": processed_game_ids,
        "total_processed": len(processed_game_ids),
        "game_traces": game_traces,
        "summary": summary,
    }
    output_path = Path(args.out) if args.out else _default_stage_output_path(args.stage)
    artifact = RunArtifact(
        run_id=output_path.stem,
        stage=args.stage,
        manifest_path=args.manifest,
        total_games=len(processed_game_ids),
        created_at=_utc_timestamp(),
        stages=[_evaluate_stage(args.stage, processed_game_ids)],
        lifts=[],
        game_traces=report["game_traces"],
        summary=report["summary"],
    )
    writer = ArtifactWriter(output_path.parent)
    json_path, _ = writer.write(artifact)
    print(f"Completed {args.stage} smoke run for {len(processed_game_ids)} games -> {json_path}")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="cuga-arc3")
    subcommands = parser.add_subparsers(dest="cmd", required=True)

    ladder = subcommands.add_parser("run-ladder")
    ladder.add_argument("--out", required=True)
    ladder.add_argument("--manifest", required=False)
    ladder.add_argument("--live", action="store_true", default=False)
    ladder.add_argument(
        "--master-prompt",
        default=None,
        help="Inline system / test master prompt (overrides manifest and env).",
    )
    ladder.add_argument(
        "--master-prompt-file",
        default=None,
        help="Path to a text/markdown file used as the test master prompt.",
    )

    stage = subcommands.add_parser("run-stage")
    stage.add_argument("--stage", required=True, choices=["S0", "S1", "S2", "S3"])
    stage.add_argument("--manifest", required=True)
    stage.add_argument("--limit", required=True, type=int)
    stage.add_argument("--out", required=False)
    stage.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Override max steps per game (default: ARC_MAX_STEPS_PER_GAME when live, else 2 for fast simulation).",
    )
    stage.add_argument(
        "--master-prompt",
        default=None,
        help="Inline system / test master prompt (overrides manifest and env).",
    )
    stage.add_argument(
        "--master-prompt-file",
        default=None,
        help="Path to a text/markdown file used as the test master prompt.",
    )

    watch = subcommands.add_parser(
        "watch-serve",
        help="HTTP server for the browser side panel (Chrome extension) while ARC-3 runs.",
    )
    watch.add_argument(
        "--artifact",
        required=True,
        type=Path,
        help="Path to run artifact JSON (same file written by run-stage).",
    )
    watch.add_argument("--host", default="127.0.0.1", help="Bind address (default 127.0.0.1).")
    watch.add_argument("--port", type=int, default=8765, help="Port (default 8765).")

    args = parser.parse_args(argv)

    if args.cmd == "run-ladder":
        manifest_path = args.manifest if args.manifest else _default_manifest_path()
        manifest = BenchmarkManifest.from_yaml_path(manifest_path)
        game_ids = _all_manifest_game_ids(manifest)
        if args.live:
            asyncio.run(_run_live_ladder_command(args, manifest, manifest_path, game_ids))
        else:
            stages = [_evaluate_stage(stage_key, game_ids) for stage_key in ["S0", "S1", "S2", "S3"]]
            baseline = stages[0]
            lifts = [stage_lift(baseline, candidate) for candidate in stages[1:]]
            output_path = Path(args.out)
            artifact = RunArtifact(
                run_id=output_path.stem,
                stage="ladder",
                manifest_path=str(manifest_path),
                total_games=len(game_ids),
                created_at=_utc_timestamp(),
                stages=stages,
                lifts=lifts,
            )
            writer = ArtifactWriter(output_path.parent)
            json_path, _ = writer.write(
                artifact,
                include_jsonl=False,
            )
            print(f"Wrote ladder report to {json_path}")

    if args.cmd == "run-stage":
        asyncio.run(_run_stage_command(args))

    if args.cmd == "watch-serve":
        run_watch_server(artifact_path=args.artifact, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
