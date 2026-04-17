from __future__ import annotations

import pytest

from cuga_arc3.eval.harness import compute_reliability_metrics
from cuga_arc3.runner.loop import RunnerLoop
from cuga_arc3.runner.scaffolds import STAGE_PROFILES


def _trace_for(loop: RunnerLoop, game_id: str) -> dict[str, object]:
    events = loop.simulate(game_id)
    return {"game_id": game_id, "events": [event.to_dict() for event in events]}


@pytest.mark.e2e
def test_abort_rate_never_exceeds_threshold_in_clean_run() -> None:
    game_ids = ["game-001", "game-002", "game-003"]

    for stage in ("S0", "S1", "S2", "S3"):
        loop = RunnerLoop(STAGE_PROFILES[stage], max_steps=3, seed=0)
        traces = [_trace_for(loop, game_id) for game_id in game_ids]
        metrics = compute_reliability_metrics(stage=stage, game_traces=traces)
        assert metrics.abort_rate == 0.0


@pytest.mark.e2e
def test_retry_run_abort_rate_reflects_exhausted_retries() -> None:
    loop = RunnerLoop(STAGE_PROFILES["S0"], max_steps=3, force_retries=10, seed=0)
    traces = [_trace_for(loop, "game-001")]
    metrics = compute_reliability_metrics(stage="S0", game_traces=traces)

    assert metrics.abort_rate == 1.0


@pytest.mark.e2e
def test_stage_s1_has_no_higher_abort_rate_than_s0_in_clean_run() -> None:
    s0_loop = RunnerLoop(STAGE_PROFILES["S0"], max_steps=3, seed=1)
    s1_loop = RunnerLoop(STAGE_PROFILES["S1"], max_steps=3, seed=1)
    s0_metrics = compute_reliability_metrics(
        stage="S0", game_traces=[_trace_for(s0_loop, "game-001")]
    )
    s1_metrics = compute_reliability_metrics(
        stage="S1", game_traces=[_trace_for(s1_loop, "game-001")]
    )

    assert s0_metrics.abort_rate == 0.0
    assert s1_metrics.abort_rate == 0.0
