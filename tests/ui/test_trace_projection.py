from __future__ import annotations

from cuga_arc3.runner.events import TraceEvent
from cuga_arc3.ui.app import project_right_panel


def test_project_right_panel_extracts_latest_plan_action_reflection() -> None:
    events = [
        TraceEvent("plan_updated", "S1", "g-1", 0, {"plan": "map board"}),
        TraceEvent("reasoning_step", "S1", "g-1", 1, {"reasoning": "prioritize anchor consistency"}),
        TraceEvent("action_proposed", "S1", "g-1", 1, {"action": 4, "rationale": "align shape"}),
        TraceEvent("reflection", "S1", "g-1", 1, {"note": "shifted focus to top-left"}),
        TraceEvent("plan_updated", "S1", "g-1", 2, {"plan": "focus bottom row"}),
        TraceEvent("action_proposed", "S1", "g-1", 2, {"action": 2, "rationale": "reduce noise"}),
        TraceEvent("reflection", "S1", "g-1", 2, {"note": "retry with cleaner anchor"}),
    ]

    panel = project_right_panel(events)

    assert panel["plan"] == "focus bottom row"
    assert panel["reasoning"] == "prioritize anchor consistency"
    assert panel["action"] == {"action": 2, "rationale": "reduce noise"}
    assert panel["reflection"] == "retry with cleaner anchor"


def test_project_right_panel_uses_action_rationale_when_reasoning_event_missing() -> None:
    events = [
        TraceEvent("plan_updated", "S0", "g-1", 0, {"plan": "find transform"}),
        TraceEvent("action_proposed", "S0", "g-1", 1, {"action": 3, "rationale": "test horizontal flip"}),
    ]

    panel = project_right_panel(events)

    assert panel["reasoning"] == "test horizontal flip"
