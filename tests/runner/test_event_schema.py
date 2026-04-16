from __future__ import annotations

from datetime import datetime

from cuga_arc3.runner.events import TraceEvent


def test_trace_event_to_dict_includes_expected_fields() -> None:
    event = TraceEvent(
        event_type="action_proposed",
        stage="S1",
        game_id="game-1",
        step_idx=3,
        payload={"action": 4},
        timestamp="2026-01-01T00:00:00+00:00",
    )

    assert event.to_dict() == {
        "event_type": "action_proposed",
        "stage": "S1",
        "game_id": "game-1",
        "step_idx": 3,
        "payload": {"action": 4},
        "timestamp": "2026-01-01T00:00:00+00:00",
    }


def test_trace_event_defaults_timestamp_to_utc_iso_string() -> None:
    event = TraceEvent(
        event_type="plan_updated",
        stage="S0",
        game_id="game-1",
        step_idx=0,
        payload={},
    )

    parsed = datetime.fromisoformat(event.timestamp)
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() is not None
    assert parsed.utcoffset().total_seconds() == 0
