from __future__ import annotations

import json
import os
from pathlib import Path

from cuga_arc3.cli import main


def test_run_ladder_writes_stages_and_lifts(tmp_path: Path) -> None:
    output_path = tmp_path / "ladder.json"

    main(["run-ladder", "--out", str(output_path)])

    assert output_path.exists()
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert [entry["stage"] for entry in report["stages"]] == ["S0", "S1", "S2", "S3"]
    assert report["lifts"] == [
        {
            "from_stage": "S0",
            "to_stage": "S1",
            "absolute_lift": 0.07,
            "relative_lift_pct": 35.0,
        },
        {
            "from_stage": "S0",
            "to_stage": "S2",
            "absolute_lift": 0.14,
            "relative_lift_pct": 70.0,
        },
        {
            "from_stage": "S0",
            "to_stage": "S3",
            "absolute_lift": 0.19,
            "relative_lift_pct": 95.0,
        },
    ]


def test_run_stage_writes_smoke_summary_for_limited_games(tmp_path: Path) -> None:
    output_path = tmp_path / "artifacts" / "stage-s0-smoke.json"
    manifest_path = (
        Path(__file__).resolve().parents[2]
        / "benchmark"
        / "manifests"
        / "arc3-core30-stress20.yaml"
    )

    previous_cwd = Path.cwd()
    try:
        # Validate CLI default --out behavior for run-stage.
        os.chdir(tmp_path)
        main(
            [
                "run-stage",
                "--stage",
                "S0",
                "--manifest",
                str(manifest_path),
                "--limit",
                "3",
            ]
        )
    finally:
        os.chdir(previous_cwd)

    assert output_path.exists()
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["stage"] == "S0"
    assert report["manifest_path"] == str(manifest_path)
    assert report["processed_game_ids"] == ["core-01", "core-02", "core-03"]
    assert report["total_processed"] == 3
    assert len(report["game_traces"]) == 3
    assert report["game_traces"][0]["game_id"] == "core-01"
    assert [event["event_type"] for event in report["game_traces"][0]["events"]] == [
        "plan_updated",
        "action_proposed",
        "action_proposed",
        "episode_end",
    ]
    assert report["summary"] == {
        "status": "smoke_complete",
        "succeeded": 3,
        "failed": 0,
        "event_counts": {
            "plan_updated": 3,
            "action_proposed": 6,
            "episode_end": 3,
        },
        "total_events": 12,
    }
