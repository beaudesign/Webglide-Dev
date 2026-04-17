from __future__ import annotations

from cuga_arc3.eval.harness import compute_live_stage_metrics
from cuga_arc3.eval.manifest import BenchmarkManifest


def test_compute_live_stage_metrics_from_traces() -> None:
    manifest = BenchmarkManifest(core=[f"core-{idx}" for idx in range(1, 6)], stress=[])
    game_traces = [
        {
            "game_id": "core-1",
            "events": [
                {"event_type": "episode_end", "payload": {"stop_reason": "solved"}},
            ],
        },
        {
            "game_id": "core-2",
            "events": [
                {"event_type": "episode_end", "payload": {"stop_reason": "solved"}},
            ],
        },
        {
            "game_id": "core-3",
            "events": [
                {"event_type": "episode_end", "payload": {"stop_reason": "max_steps_reached"}},
            ],
        },
        {
            "game_id": "core-4",
            "events": [
                {"event_type": "episode_end", "payload": {"stop_reason": "solved"}},
            ],
        },
        {
            "game_id": "core-5",
            "events": [
                {"event_type": "episode_end", "payload": {"stop_reason": "max_steps_reached"}},
            ],
        },
    ]

    metrics = compute_live_stage_metrics(stage="S2", game_traces=game_traces, manifest=manifest)

    assert metrics.stage == "S2"
    assert metrics.solved_count == 3
    assert metrics.total_games == 5
    assert metrics.win_rate == 0.6


def test_compute_live_stage_metrics_none_solved() -> None:
    manifest = BenchmarkManifest(core=["core-1", "core-2", "core-3"], stress=[])
    game_traces = [
        {
            "game_id": "core-1",
            "events": [
                {"event_type": "episode_end", "payload": {"stop_reason": "max_steps_reached"}},
            ],
        },
        {
            "game_id": "core-2",
            "events": [
                {"event_type": "episode_end", "payload": {"stop_reason": "max_steps_reached"}},
            ],
        },
        {
            "game_id": "core-3",
            "events": [
                {"event_type": "episode_end", "payload": {"stop_reason": "max_steps_reached"}},
            ],
        },
    ]

    metrics = compute_live_stage_metrics(stage="S0", game_traces=game_traces, manifest=manifest)

    assert metrics.solved_count == 0
    assert metrics.total_games == 3
    assert metrics.win_rate == 0.0
