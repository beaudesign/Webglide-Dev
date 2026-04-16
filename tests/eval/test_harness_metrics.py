from __future__ import annotations

from cuga_arc3.eval.harness import compute_stage_metrics


def test_compute_stage_metrics_win_rate_for_25_of_50() -> None:
    metrics = compute_stage_metrics(stage="S0", wins=25, total_games=50)

    assert metrics.stage == "S0"
    assert metrics.wins == 25
    assert metrics.total_games == 50
    assert metrics.win_rate == 0.5
