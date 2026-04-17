from __future__ import annotations

from typing import Any

import streamlit as st

from cuga_arc3.runner.events import (
    PAYLOAD_KEY_RETRY_COUNT,
    PAYLOAD_KEY_STATE,
    PAYLOAD_KEY_STOP_REASON,
    TraceEvent,
)
from cuga_arc3.ui.diagnostics import DiagnosticsPanel, project_diagnostics


def project_right_panel(events: list[TraceEvent]) -> dict[str, Any]:
    plan = ""
    action: dict[str, Any] = {}
    reasoning = ""
    reflection = ""

    for event in events:
        if event.event_type == "plan_updated":
            plan = str(event.payload.get("plan", ""))
        elif event.event_type == "reasoning_step":
            reasoning = str(event.payload.get("reasoning", ""))
        elif event.event_type == "action_proposed":
            action = dict(event.payload)
            if not reasoning:
                reasoning = str(event.payload.get("rationale", ""))
        elif event.event_type == "reflection":
            reflection = str(event.payload.get("note", ""))

    return {
        "plan": plan,
        "reasoning": reasoning,
        "action": action,
        "reflection": reflection,
    }


def render(events: list[TraceEvent]) -> None:
    left, right = st.columns([2, 1])

    with left:
        st.subheader("Run Overview")
        st.write("ARC-3 stage execution")

    with right:
        st.subheader("Planning + Reasoning")
        panel: DiagnosticsPanel = project_diagnostics(events)
        st.markdown("**Plan**")
        st.write(panel.plan)
        st.markdown("**Reasoning**")
        st.write(panel.reasoning)
        st.markdown("**Action**")
        st.json(panel.action)
        st.markdown("**Reflection**")
        st.write(panel.reflection)

        st.subheader("Reliability")
        st.markdown("**Current state**")
        st.write(panel.current_state or "—")
        st.markdown("**Policy**")
        if panel.last_policy_decision:
            st.json(panel.last_policy_decision)
        else:
            st.write("None")
        st.markdown("**Retries**")
        st.write(panel.retry_count)
        st.markdown("**Stop reason**")
        st.write(panel.stop_reason or "in-progress")

        st.subheader("Health")
        for warning in panel.health_warnings:
            st.warning(warning)


def _default_events() -> list[TraceEvent]:
    return [
        TraceEvent("plan_updated", "S1", "demo-game", 0, {"plan": "scan board for anchor cells"}),
        TraceEvent(
            "reasoning_step",
            "S1",
            "demo-game",
            1,
            {"reasoning": "identify stable symmetry candidates before action"},
        ),
        TraceEvent(
            "action_proposed",
            "S1",
            "demo-game",
            1,
            {"action": 4, "rationale": "apply candidate transform"},
        ),
        TraceEvent(
            "policy_gate",
            "S1",
            "demo-game",
            1,
            {"action": 4, "allowed": True, "reason": "within threshold", "policy": "default"},
        ),
        TraceEvent("reflection", "S1", "demo-game", 1, {"note": "keep anchor fixed, expand pattern"}),
        TraceEvent(
            "episode_end",
            "S1",
            "demo-game",
            1,
            {
                PAYLOAD_KEY_STOP_REASON: "solved",
                PAYLOAD_KEY_RETRY_COUNT: 1,
                PAYLOAD_KEY_STATE: "complete",
                "status": "terminated",
            },
        ),
    ]


def main() -> None:
    render(_default_events())


if __name__ == "__main__":
    main()
