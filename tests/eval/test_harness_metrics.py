from __future__ import annotations

from cuga_arc3.eval.harness import compute_stage_metrics
from cuga_arc3.eval.manifest import BenchmarkManifest


def test_compute_stage_metrics_win_rate_for_25_of_50() -> None:
    manifest = BenchmarkManifest.from_dict(
        {
            "core": [f"core-{idx:02d}" for idx in range(1, 31)],
            "stress": [f"stress-{idx:02d}" for idx in range(1, 21)],
        }
    )
    solved_game_ids = (
        [f"core-{idx:02d}" for idx in range(1, 11)]
        + [f"stress-{idx:02d}" for idx in range(1, 16)]
        + ["stress-01", "unknown-1", "unknown-2"]
    )

    metrics = compute_stage_metrics(
        stage="S0", solved_game_ids=solved_game_ids, manifest=manifest
    )

    assert metrics.stage == "S0"
    assert metrics.solved_count == 25
    assert metrics.total_games == 50
    assert metrics.win_rate == 0.5
