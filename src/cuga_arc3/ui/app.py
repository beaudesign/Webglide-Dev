from __future__ import annotations

import json
from pathlib import Path
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
    master_prompt = ""

    for event in events:
        if event.event_type == "test_session":
            master_prompt = str(event.payload.get("master_prompt", ""))
        elif event.event_type == "plan_updated":
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
        "master_prompt": master_prompt,
    }


def _load_events_from_artifact_json(artifact_path: Path, game_id: str) -> list[TraceEvent]:
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    traces = payload.get("game_traces")
    if not isinstance(traces, list):
        return []
    for trace in traces:
        if not isinstance(trace, dict):
            continue
        if trace.get("game_id") != game_id:
            continue
        raw_events = trace.get("events")
        if not isinstance(raw_events, list):
            return []
        return [_trace_event_from_dict(row) for row in raw_events if isinstance(row, dict)]
    return []


def _trace_event_from_dict(row: dict[str, Any]) -> TraceEvent:
    event_payload = row.get("payload", {})
    return TraceEvent(
        event_type=str(row["event_type"]),
        stage=str(row["stage"]),
        game_id=str(row["game_id"]),
        step_idx=int(row["step_idx"]),
        payload=dict(event_payload) if isinstance(event_payload, dict) else {},
        timestamp=str(row.get("timestamp", "")),
    )


def _game_ids_from_artifact(artifact_path: Path) -> list[str]:
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    traces = payload.get("game_traces")
    if not isinstance(traces, list):
        return []
    ids: list[str] = []
    for trace in traces:
        if isinstance(trace, dict) and isinstance(trace.get("game_id"), str):
            ids.append(trace["game_id"])
    return ids


def render(events: list[TraceEvent]) -> None:
    left, right = st.columns([2, 1])

    with left:
        st.subheader("Run Overview")
        st.write("ARC-3 stage execution")

    with right:
        st.subheader("Planning + Reasoning")
        panel: DiagnosticsPanel = project_diagnostics(events)
        st.markdown("**Master prompt (test)**")
        if panel.master_prompt:
            st.text_area(
                "System instruction recorded for this episode",
                value=panel.master_prompt,
                height=min(320, 120 + panel.master_prompt.count("\n") * 20),
                disabled=True,
                label_visibility="collapsed",
            )
        else:
            st.caption("No `test_session` event — run with `--master-prompt-file` or manifest `master_prompt`.")

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
        TraceEvent(
            "test_session",
            "S1",
            "demo-game",
            0,
            {
                "role": "system",
                "master_prompt": "You are taking ARC-AGI-3. Hypothesize transforms, act minimally, revise on feedback.",
            },
        ),
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


def _render_watch_console() -> None:
    st.title("ARC-3 — watch the run")
    st.caption(
        "Load a run artifact (`.json` from `cuga-arc3 run-stage`) to replay traces like a computer-use session."
    )

    with st.sidebar:
        st.header("Replay")
        default_guess = Path("artifacts") / "stage-s0-smoke.json"
        path_str = st.text_input(
            "Artifact JSON path",
            value=str(default_guess) if default_guess.exists() else "",
            help="Written by `run-stage` / `run-ladder` (same stem as optional `.jsonl`).",
        )
        st.caption("While a long `run-stage` is writing, click **Reload** to pull new events.")

    artifact_path = Path(path_str).expanduser() if path_str.strip() else None
    if artifact_path is None or not artifact_path.is_file():
        st.info("Enter a valid artifact path, or run a stage first to create `artifacts/*.json`.")
        render(_default_events())
        st.subheader("Event timeline (demo)")
        for idx, event in enumerate(_default_events()):
            with st.expander(f"{idx + 1}. `{event.event_type}` · step {event.step_idx}"):
                st.json(event.to_dict())
        return

    game_ids = _game_ids_from_artifact(artifact_path)
    if not game_ids:
        st.warning("No `game_traces` in this artifact.")
        return

    if "watch_game_id" not in st.session_state or st.session_state.watch_game_id not in game_ids:
        st.session_state.watch_game_id = game_ids[0]

    with st.sidebar:
        selected = st.selectbox("Game", options=game_ids, index=game_ids.index(st.session_state.watch_game_id))
        st.session_state.watch_game_id = selected
        doc_link = "https://docs.arcprize.org"
        st.markdown(f"[ARC Prize docs]({doc_link}) · [ARC-3 API host](https://three.arcprize.org)")
        if st.button("Reload artifact"):
            st.rerun()

    events = _load_events_from_artifact_json(artifact_path, selected)
    meta = json.loads(artifact_path.read_text(encoding="utf-8"))

    st.subheader(f"Episode · `{selected}`")
    cols = st.columns(3)
    with cols[0]:
        st.metric("Stage", str(meta.get("stage", "—")))
    with cols[1]:
        st.metric("Events", len(events))
    with cols[2]:
        st.metric("Manifest", Path(str(meta.get("manifest_path", ""))).name or "—")

    timeline, inspector = st.columns([11, 9])
    with timeline:
        st.markdown("### Timeline (computer-use trace)")
        for idx, event in enumerate(events):
            title = f"{idx + 1}. `{event.event_type}` · step {event.step_idx}"
            with st.expander(title, expanded=(idx >= len(events) - 3)):
                st.json(event.to_dict())
    with inspector:
        st.markdown("### Operator panel")
        render(events)


def main() -> None:
    st.set_page_config(page_title="CUGA ARC-3", layout="wide")
    _render_watch_console()


if __name__ == "__main__":
    main()
