from __future__ import annotations

from pathlib import Path

from cuga_arc3.artifacts.schema import RunArtifact
from cuga_arc3.artifacts.writer import ArtifactWriter
from cuga_arc3.runner.events import PAYLOAD_KEY_STOP_REASON, TraceEvent
from cuga_arc3.ui.diagnostics import load_jsonl_traces


def test_load_jsonl_traces_from_real_artifact(tmp_path: Path) -> None:
    expected_events = [
        TraceEvent(
            "plan_updated",
            "S0",
            "core-01",
            0,
            {"plan": "map board"},
            timestamp="2026-01-01T00:00:00+00:00",
        ),
        TraceEvent(
            "episode_end",
            "S0",
            "core-01",
            1,
            {PAYLOAD_KEY_STOP_REASON: "solved"},
            timestamp="2026-01-01T00:00:01+00:00",
        ),
    ]
    artifact = RunArtifact(
        run_id="run-replay",
        stage="S0",
        manifest_path="benchmark/manifests/arc3-core30-stress20.yaml",
        total_games=1,
        created_at="2026-01-01T00:00:00+00:00",
        stages=[{"stage": "S0", "solved_count": 1, "total_games": 1, "win_rate": 1.0}],
        lifts=[],
        game_traces=[{"game_id": "core-01", "events": [event.to_dict() for event in expected_events]}],
        summary={"status": "ok"},
    )
    writer = ArtifactWriter(tmp_path)

    _, jsonl_path = writer.write(artifact)
    assert jsonl_path is not None

    loaded_events = load_jsonl_traces(jsonl_path)

    assert loaded_events == expected_events
