from __future__ import annotations


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
