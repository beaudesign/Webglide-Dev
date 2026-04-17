from __future__ import annotations

import json
from pathlib import Path

from cuga_arc3.artifacts.schema import RunArtifact
from cuga_arc3.artifacts.writer import ArtifactWriter


def _sample_artifact(*, run_id: str = "run-xyz", with_traces: bool = True) -> RunArtifact:
    traces = (
        [
            {
                "game_id": "core-01",
                "events": [
                    {"event_type": "plan_updated", "game_id": "core-01", "step_idx": 0},
                    {"event_type": "episode_end", "game_id": "core-01", "step_idx": 1},
                ],
            },
            {
                "game_id": "core-02",
                "events": [{"event_type": "episode_end", "game_id": "core-02", "step_idx": 0}],
            },
        ]
        if with_traces
        else []
    )
    return RunArtifact(
        run_id=run_id,
        stage="S0",
        manifest_path="benchmark/manifests/arc3-core30-stress20.yaml",
        total_games=2,
        created_at="2026-01-01T00:00:00+00:00",
        stages=[{"stage": "S0", "solved_count": 1, "total_games": 2, "win_rate": 0.5}],
        lifts=[],
        game_traces=traces,
        summary={"status": "ok"},
    )


def test_write_produces_json_and_jsonl_files(tmp_path: Path) -> None:
    artifact = _sample_artifact(with_traces=True)
    writer = ArtifactWriter(tmp_path)

    json_path, jsonl_path = writer.write(artifact)

    assert json_path == tmp_path / f"{artifact.run_id}.json"
    assert json_path.exists()
    assert jsonl_path == tmp_path / f"{artifact.run_id}.jsonl"
    assert jsonl_path is not None
    assert jsonl_path.exists()
    written_payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert written_payload["run_id"] == artifact.run_id
    flat_events = [
        {"event_type": "plan_updated", "game_id": "core-01", "step_idx": 0},
        {"event_type": "episode_end", "game_id": "core-01", "step_idx": 1},
        {"event_type": "episode_end", "game_id": "core-02", "step_idx": 0},
    ]
    lines = jsonl_path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line) for line in lines] == flat_events


def test_write_json_only_when_no_traces(tmp_path: Path) -> None:
    artifact = _sample_artifact(with_traces=False)
    writer = ArtifactWriter(tmp_path)

    json_path, jsonl_path = writer.write(artifact)

    assert json_path.exists()
    assert jsonl_path is None
    assert not (tmp_path / f"{artifact.run_id}.jsonl").exists()


def test_load_round_trips_artifact(tmp_path: Path) -> None:
    artifact = _sample_artifact(with_traces=True)
    writer = ArtifactWriter(tmp_path)
    writer.write(artifact)

    loaded = writer.load(artifact.run_id)

    assert loaded == artifact
