from __future__ import annotations

import json
from pathlib import Path

from cuga_arc3.runner.events import (
    PAYLOAD_KEY_RETRY_COUNT,
    PAYLOAD_KEY_STOP_REASON,
    TraceEvent,
)
from cuga_arc3.ui.diagnostics import load_jsonl_traces, project_diagnostics


def test_project_diagnostics_extracts_master_prompt() -> None:
    events = [
        TraceEvent(
            "test_session",
            "S0",
            "g-1",
            0,
            {"role": "system", "master_prompt": "Do the benchmark carefully."},
        ),
        TraceEvent("plan_updated", "S0", "g-1", 0, {"plan": "x"}),
        TraceEvent("episode_end", "S0", "g-1", 1, {PAYLOAD_KEY_STOP_REASON: "solved"}),
    ]

    panel = project_diagnostics(events)

    assert panel.master_prompt == "Do the benchmark carefully."


def test_project_diagnostics_extracts_stop_reason() -> None:
    events = [
        TraceEvent("plan_updated", "S1", "g-1", 0, {"plan": "scan anchors"}),
        TraceEvent(
            "episode_end",
            "S1",
            "g-1",
            2,
            {PAYLOAD_KEY_STOP_REASON: "solved", PAYLOAD_KEY_RETRY_COUNT: 1},
        ),
    ]

    panel = project_diagnostics(events)

    assert panel.stop_reason == "solved"


def test_project_diagnostics_extracts_policy_decision() -> None:
    events = [
        TraceEvent("plan_updated", "S1", "g-1", 0, {"plan": "map board"}),
        TraceEvent("policy_gate", "S1", "g-1", 1, {"allowed": True, "policy": "strict"}),
        TraceEvent("policy_gate", "S1", "g-1", 2, {"allowed": False, "policy": "strict"}),
        TraceEvent("episode_end", "S1", "g-1", 2, {PAYLOAD_KEY_STOP_REASON: "aborted"}),
    ]

    panel = project_diagnostics(events)

    assert panel.last_policy_decision == {"allowed": False, "policy": "strict"}


def test_project_diagnostics_retry_count_from_episode_end() -> None:
    events = [
        TraceEvent("plan_updated", "S2", "g-2", 0, {"plan": "test transform"}),
        TraceEvent(
            "episode_end",
            "S2",
            "g-2",
            5,
            {PAYLOAD_KEY_RETRY_COUNT: 3, PAYLOAD_KEY_STOP_REASON: "max_steps_reached"},
        ),
    ]

    panel = project_diagnostics(events)

    assert panel.retry_count == 3


def test_project_diagnostics_warns_missing_episode_end() -> None:
    events = [TraceEvent("plan_updated", "S0", "g-0", 0, {"plan": "try symmetry"})]

    panel = project_diagnostics(events)

    assert "missing episode_end" in panel.health_warnings
    assert "missing plan" not in panel.health_warnings


def test_load_jsonl_traces_round_trips_events(tmp_path: Path) -> None:
    expected_events = [
        TraceEvent(
            "plan_updated",
            "S1",
            "g-1",
            0,
            {"plan": "scan board"},
            timestamp="2026-01-01T00:00:00+00:00",
        ),
        TraceEvent(
            "episode_end",
            "S1",
            "g-1",
            1,
            {PAYLOAD_KEY_STOP_REASON: "solved", PAYLOAD_KEY_RETRY_COUNT: 0},
            timestamp="2026-01-01T00:00:01+00:00",
        ),
    ]
    jsonl_path = tmp_path / "events.jsonl"
    jsonl_path.write_text(
        "\n".join(json.dumps(event.to_dict()) for event in expected_events) + "\n",
        encoding="utf-8",
    )

    loaded_events = load_jsonl_traces(jsonl_path)

    assert loaded_events == expected_events
