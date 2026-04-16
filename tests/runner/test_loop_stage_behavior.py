from __future__ import annotations

from cuga_arc3.runner.loop import RunnerLoop


def test_simulate_emits_reflection_events_for_s1() -> None:
    loop = RunnerLoop(stage="S1", max_steps=2)

    events = loop.simulate(game_id="game-1")
    event_types = [event.event_type for event in events]

    assert event_types == [
        "plan_updated",
        "action_proposed",
        "reflection",
        "action_proposed",
        "reflection",
        "episode_end",
    ]


def test_simulate_does_not_emit_reflection_events_for_s0() -> None:
    loop = RunnerLoop(stage="S0", max_steps=2)

    events = loop.simulate(game_id="game-1")
    event_types = [event.event_type for event in events]

    assert event_types == [
        "plan_updated",
        "action_proposed",
        "action_proposed",
        "episode_end",
    ]
