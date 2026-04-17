from __future__ import annotations

import pytest

from cuga_arc3.artifacts.schema import ARTIFACT_VERSION, RunArtifact


def _sample_artifact() -> RunArtifact:
    return RunArtifact(
        run_id="run-123",
        stage="S0",
        manifest_path="benchmark/manifests/arc3-core30-stress20.yaml",
        total_games=3,
        created_at="2026-01-01T00:00:00+00:00",
        stages=[{"stage": "S0", "solved_count": 1, "total_games": 3, "win_rate": 0.33}],
        lifts=[{"from_stage": "S0", "to_stage": "S1", "absolute_delta": 0.1, "relative_delta": 0.3}],
        game_traces=[{"game_id": "core-01", "events": [{"event_type": "episode_end"}]}],
        summary={"status": "ok"},
    )


def test_run_artifact_serializes_version_field() -> None:
    artifact = _sample_artifact()

    payload = artifact.to_dict()

    assert payload["artifact_version"] == ARTIFACT_VERSION


def test_run_artifact_round_trips_via_dict() -> None:
    artifact = _sample_artifact()

    round_tripped = RunArtifact.from_dict(artifact.to_dict())

    assert round_tripped == artifact


def test_from_dict_rejects_wrong_version() -> None:
    artifact = _sample_artifact()
    payload = artifact.to_dict()
    payload["artifact_version"] = "0.9"

    with pytest.raises(ValueError, match="artifact_version"):
        RunArtifact.from_dict(payload)
