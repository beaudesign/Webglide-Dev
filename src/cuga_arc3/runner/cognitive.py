from __future__ import annotations

from cuga_arc3.runner.events import TraceEvent


def plan_frame(
    stage: str, game_id: str, step_idx: int, observation: dict[str, object]
) -> TraceEvent:
    _ = observation
    return TraceEvent(
        event_type="reasoning_step",
        stage=stage,
        game_id=game_id,
        step_idx=step_idx,
        payload={
            "reasoning": "S1 structured plan: analyse board state and identify candidate transform"
        },
    )


def reflection_note(
    stage: str, game_id: str, step_idx: int, observation: dict[str, object]
) -> TraceEvent:
    _ = observation
    return TraceEvent(
        event_type="reflection",
        stage=stage,
        game_id=game_id,
        step_idx=step_idx,
        payload={
            "note": "S1 reflection: verify transform consistency before next step"
        },
    )
