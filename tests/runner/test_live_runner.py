from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from cuga_arc3.runner.events import PAYLOAD_KEY_STOP_REASON
from cuga_arc3.runner.loop import RunnerLoop
from cuga_arc3.runner.scaffolds import STAGE_PROFILES


def _mock_client(execute_action: AsyncMock | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        reset_or_start=AsyncMock(return_value={"guid": "test-guid"}),
        execute_action=execute_action
        or AsyncMock(return_value={"status": "in_progress", "score": 0}),
    )


@pytest.mark.asyncio
async def test_live_runner_emits_test_session_when_master_prompt_set() -> None:
    runner = RunnerLoop(
        stage_profile=STAGE_PROFILES["S0"],
        max_steps=1,
        master_prompt="ARC-3 system instruction",
    )
    client = _mock_client()

    events = await runner.run(game_id="game-prompt", client=client, card_id="card-1")

    session_events = [event for event in events if event.event_type == "test_session"]
    assert len(session_events) == 1
    assert session_events[0].payload["master_prompt"] == "ARC-3 system instruction"


@pytest.mark.asyncio
async def test_live_runner_completes_after_max_steps() -> None:
    runner = RunnerLoop(stage_profile=STAGE_PROFILES["S0"], max_steps=2)
    client = _mock_client()

    events = await runner.run(game_id="game-live-max-steps", client=client, card_id="card-1")
    episode_end = [event for event in events if event.event_type == "episode_end"][-1]

    client.reset_or_start.assert_awaited_once_with(
        game_id="game-live-max-steps",
        card_id="card-1",
    )
    assert client.execute_action.await_count == 2
    assert episode_end.payload[PAYLOAD_KEY_STOP_REASON] == "max_steps_reached"


@pytest.mark.asyncio
async def test_live_runner_marks_solved_when_api_returns_solved() -> None:
    runner = RunnerLoop(stage_profile=STAGE_PROFILES["S0"], max_steps=5)
    client = _mock_client(execute_action=AsyncMock(return_value={"status": "solved"}))

    events = await runner.run(game_id="game-live-solved", client=client, card_id="card-1")
    episode_end = [event for event in events if event.event_type == "episode_end"][-1]

    assert episode_end.payload[PAYLOAD_KEY_STOP_REASON] == "solved"


@pytest.mark.asyncio
async def test_live_runner_retries_on_http_error() -> None:
    request = httpx.Request("POST", "https://three.arcprize.org/commands/action1")
    response = httpx.Response(status_code=500, request=request)
    error = httpx.HTTPStatusError(
        "Server error while executing action",
        request=request,
        response=response,
    )
    execute_action = AsyncMock(
        side_effect=[
            error,
            {"status": "in_progress", "score": 0},
        ]
    )
    runner = RunnerLoop(stage_profile=STAGE_PROFILES["S0"], max_steps=1)
    client = _mock_client(execute_action=execute_action)

    events = await runner.run(game_id="game-live-retry", client=client, card_id="card-1")

    retry_events = [event for event in events if event.event_type == "retry"]
    errored_actions = [
        event
        for event in events
        if event.event_type == "action_proposed" and "error" in event.payload
    ]

    assert retry_events
    assert errored_actions
    assert "500" in str(errored_actions[0].payload["error"])
