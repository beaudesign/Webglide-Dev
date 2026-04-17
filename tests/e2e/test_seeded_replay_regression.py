from __future__ import annotations

from pathlib import Path

import pytest

from cuga_arc3.artifacts.schema import RunArtifact
from cuga_arc3.artifacts.writer import ArtifactWriter
from cuga_arc3.runner.loop import RunnerLoop
from cuga_arc3.runner.scaffolds import STAGE_PROFILES


def _game_trace(game_id: str, loop: RunnerLoop) -> dict[str, object]:
    events = loop.simulate(game_id)
    return {"game_id": game_id, "events": [event.to_dict() for event in events]}


@pytest.mark.e2e
def test_same_seed_same_stage_produces_identical_events() -> None:
    run1 = RunnerLoop(STAGE_PROFILES["S1"], max_steps=5, seed=42).simulate("game-abc")
    run2 = RunnerLoop(STAGE_PROFILES["S1"], max_steps=5, seed=42).simulate("game-abc")

    assert [event.event_type for event in run1] == [event.event_type for event in run2]
    assert [event.step_idx for event in run1] == [event.step_idx for event in run2]


@pytest.mark.e2e
def test_different_game_ids_same_seed_produces_same_shape() -> None:
    events_a = RunnerLoop(STAGE_PROFILES["S0"], max_steps=3, seed=0).simulate("game-001")
    events_b = RunnerLoop(STAGE_PROFILES["S0"], max_steps=3, seed=0).simulate("game-002")

    assert [event.event_type for event in events_a] == [
        event.event_type for event in events_b
    ]


@pytest.mark.e2e
def test_artifact_writer_round_trip_preserves_event_count(tmp_path: Path) -> None:
    loop = RunnerLoop(STAGE_PROFILES["S1"], max_steps=4, seed=7)
    game_ids = ["game-001", "game-002", "game-003"]
    game_traces = [_game_trace(game_id, loop) for game_id in game_ids]
    artifact = RunArtifact(
        run_id="seeded-replay-round-trip",
        stage="S1",
        manifest_path="benchmark/manifests/arc3-core30-stress20.yaml",
        total_games=len(game_ids),
        created_at="2026-01-01T00:00:00+00:00",
        stages=[{"stage": "S1", "solved_count": 0, "total_games": len(game_ids)}],
        lifts=[],
        game_traces=game_traces,
        summary={"status": "ok"},
    )
    writer = ArtifactWriter(tmp_path)

    writer.write(artifact)
    loaded = writer.load(artifact.run_id)

    assert len(loaded.game_traces) == len(game_traces)
    assert loaded.game_traces == game_traces
