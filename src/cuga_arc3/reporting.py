from __future__ import annotations

from cuga_arc3.eval.harness import ReliabilityMetrics


def stage_lift(
    baseline: dict[str, str | float], candidate: dict[str, str | float]
) -> dict[str, str | float]:
    baseline_win_rate = float(baseline["win_rate"])
    candidate_win_rate = float(candidate["win_rate"])
    absolute_lift = round(candidate_win_rate - baseline_win_rate, 2)
    if baseline_win_rate == 0:
        relative_lift_pct = 0.0
    else:
        relative_lift_pct = round((absolute_lift / baseline_win_rate) * 100, 2)

    return {
        "from_stage": str(baseline["stage"]),
        "to_stage": str(candidate["stage"]),
        "absolute_lift": absolute_lift,
        "relative_lift_pct": relative_lift_pct,
    }


def reliability_delta(
    baseline: ReliabilityMetrics, candidate: ReliabilityMetrics
) -> dict[str, str | float | int]:
    return {
        "from_stage": baseline.stage,
        "to_stage": candidate.stage,
        "abort_rate_delta": round(candidate.abort_rate - baseline.abort_rate, 4),
        "mean_retries_delta": round(
            candidate.mean_retries - baseline.mean_retries,
            4,
        ),
        "invalid_action_delta": (
            candidate.invalid_action_count - baseline.invalid_action_count
        ),
    }
