from __future__ import annotations

from cuga_arc3.runner.events import (
    PAYLOAD_KEY_RETRY_COUNT,
    PAYLOAD_KEY_STATE,
    PAYLOAD_KEY_STOP_REASON,
)
from cuga_arc3.runner.loop import RunnerLoop
from cuga_arc3.runner.scaffolds import STAGE_PROFILES


def test_simulate_emits_reflection_events_for_s1() -> None:
    loop = RunnerLoop(stage_profile=STAGE_PROFILES["S1"], max_steps=2)

    events = loop.simulate(game_id="game-1")
    assert [event.event_type for event in events] == [
        "plan_updated",
        "action_proposed",
        "reflection",
        "action_proposed",
        "reflection",
        "episode_end",
    ]
    assert [event.step_idx for event in events] == [0, 1, 1, 2, 2, 2]
    assert [event.payload for event in events] == [
        {"plan": "initial plan"},
        {"action": 1, "rationale": "default action policy"},
        {"note": "adjust next action from observation"},
        {"action": 1, "rationale": "default action policy"},
        {"note": "adjust next action from observation"},
        {
            "status": "terminated",
            PAYLOAD_KEY_STOP_REASON: "max_steps_reached",
            PAYLOAD_KEY_RETRY_COUNT: 0,
            PAYLOAD_KEY_STATE: "COMPLETE",
        },
    ]


def test_simulate_does_not_emit_reflection_events_for_s0() -> None:
    loop = RunnerLoop(stage_profile=STAGE_PROFILES["S0"], max_steps=2)

    events = loop.simulate(game_id="game-1")
    assert [event.event_type for event in events] == [
        "plan_updated",
        "action_proposed",
        "action_proposed",
        "episode_end",
    ]
    assert [event.step_idx for event in events] == [0, 1, 2, 2]
    assert [event.payload for event in events] == [
        {"plan": "initial plan"},
        {"action": 1, "rationale": "default action policy"},
        {"action": 1, "rationale": "default action policy"},
        {
            "status": "terminated",
            PAYLOAD_KEY_STOP_REASON: "max_steps_reached",
            PAYLOAD_KEY_RETRY_COUNT: 0,
            PAYLOAD_KEY_STATE: "COMPLETE",
        },
    ]
