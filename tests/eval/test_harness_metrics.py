from __future__ import annotations

from cuga_arc3.eval.harness import compute_stage_metrics
from cuga_arc3.eval.manifest import BenchmarkManifest
from cuga_arc3.reporting import stage_lift


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


def test_stage_lift_from_baseline() -> None:
    baseline = {"stage": "S0", "win_rate": 0.22}
    candidate = {"stage": "S2", "win_rate": 0.36}

    report = stage_lift(baseline, candidate)

    assert report["absolute_lift"] == 0.14
    assert report["relative_lift_pct"] == 63.64


def test_compute_stage_metrics_handles_empty_manifest() -> None:
    manifest = BenchmarkManifest(core=[], stress=[])

    metrics = compute_stage_metrics(stage="S0", solved_game_ids=["unknown"], manifest=manifest)

    assert metrics.solved_count == 0
    assert metrics.total_games == 0
    assert metrics.win_rate == 0.0


def test_compute_stage_metrics_deduplicates_solved_game_ids() -> None:
    manifest = BenchmarkManifest(core=["core-01", "core-02"], stress=[])

    metrics = compute_stage_metrics(
        stage="S1",
        solved_game_ids=["core-01", "core-01", "core-02", "outside"],
        manifest=manifest,
    )

    assert metrics.solved_count == 2
    assert metrics.total_games == 2
    assert metrics.win_rate == 1.0
