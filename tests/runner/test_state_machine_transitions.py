from __future__ import annotations

from cuga_arc3.runner.events import (
    PAYLOAD_KEY_RETRY_COUNT,
    PAYLOAD_KEY_STOP_REASON,
)
from cuga_arc3.runner.loop import RunnerLoop
from cuga_arc3.runner.scaffolds import STAGE_PROFILES


def _last_episode_end_payload(loop: RunnerLoop, game_id: str) -> dict[str, object]:
    events = loop.simulate(game_id=game_id)
    episode_end = [event for event in events if event.event_type == "episode_end"][-1]
    return episode_end.payload


def test_s0_loop_completes_with_max_steps_stop_reason() -> None:
    loop = RunnerLoop(stage_profile=STAGE_PROFILES["S0"], max_steps=2)

    payload = _last_episode_end_payload(loop=loop, game_id="game-s0")
    assert payload[PAYLOAD_KEY_STOP_REASON] == "max_steps_reached"


def test_s1_loop_includes_reflection_before_episode_end() -> None:
    loop = RunnerLoop(stage_profile=STAGE_PROFILES["S1"], max_steps=2)

    events = loop.simulate(game_id="game-s1")
    reflection_positions = [
        idx for idx, event in enumerate(events) if event.event_type == "reflection"
    ]
    episode_end_position = max(
        idx for idx, event in enumerate(events) if event.event_type == "episode_end"
    )

    assert reflection_positions
    assert max(reflection_positions) < episode_end_position


def test_retry_increments_emit_retry_event_then_complete() -> None:
    loop = RunnerLoop(stage_profile=STAGE_PROFILES["S0"], max_steps=2, force_retries=1)

    events = loop.simulate(game_id="game-retry")
    retry_events = [event for event in events if event.event_type == "retry"]
    episode_end = [event for event in events if event.event_type == "episode_end"][-1]

    assert retry_events
    assert episode_end.payload[PAYLOAD_KEY_RETRY_COUNT] > 0


def test_abort_emitted_when_retries_exhausted() -> None:
    max_retries = 3
    loop = RunnerLoop(
        stage_profile=STAGE_PROFILES["S0"],
        max_steps=2,
        force_retries=max_retries + 1,
        max_retries=max_retries,
    )

    payload = _last_episode_end_payload(loop=loop, game_id="game-abort")
    assert payload[PAYLOAD_KEY_STOP_REASON] == "aborted_max_retries"
