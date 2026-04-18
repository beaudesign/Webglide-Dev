from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cuga_arc3.runner.events import PAYLOAD_KEY_RETRY_COUNT, PAYLOAD_KEY_STOP_REASON, TraceEvent


@dataclass(frozen=True)
class DiagnosticsPanel:
    plan: str
    reasoning: str
    action: dict[str, Any]
    reflection: str
    master_prompt: str
    current_state: str
    last_policy_decision: dict[str, Any]
    retry_count: int
    stop_reason: str
    health_warnings: list[str]


def project_diagnostics(events: list[TraceEvent]) -> DiagnosticsPanel:
    plan = ""
    reasoning = ""
    action: dict[str, Any] = {}
    reflection = ""
    master_prompt = ""
    current_state = ""
    last_policy_decision: dict[str, Any] = {}
    retry_count = 0
    stop_reason = ""
    has_episode_end = False

    for event in events:
        payload = event.payload
        state = payload.get("state")
        if state is not None:
            current_state = str(state)

        if event.event_type == "test_session":
            master_prompt = str(payload.get("master_prompt", ""))
        elif event.event_type == "plan_updated":
            plan = str(payload.get("plan", ""))
        elif event.event_type == "reasoning_step":
            reasoning = str(payload.get("reasoning", ""))
        elif event.event_type == "action_proposed":
            action = dict(payload)
            if not reasoning:
                reasoning = str(payload.get("rationale", ""))
        elif event.event_type == "reflection":
            reflection = str(payload.get("note", ""))
        elif event.event_type == "policy_gate":
            last_policy_decision = dict(payload)
        elif event.event_type == "episode_end":
            has_episode_end = True
            retry_count = _coerce_retry_count(payload.get(PAYLOAD_KEY_RETRY_COUNT, 0))
            stop_reason = str(payload.get(PAYLOAD_KEY_STOP_REASON, ""))

    health_warnings: list[str] = []
    if not has_episode_end:
        health_warnings.append("missing episode_end")
    if not plan:
        health_warnings.append("missing plan")

    return DiagnosticsPanel(
        plan=plan,
        reasoning=reasoning,
        action=action,
        reflection=reflection,
        master_prompt=master_prompt,
        current_state=current_state,
        last_policy_decision=last_policy_decision,
        retry_count=retry_count,
        stop_reason=stop_reason,
        health_warnings=health_warnings,
    )


def load_jsonl_traces(jsonl_path: Path) -> list[TraceEvent]:
    events: list[TraceEvent] = []
    with jsonl_path.open(encoding="utf-8") as jsonl_file:
        for raw_line in jsonl_file:
            line = raw_line.strip()
            if not line:
                continue
            payload = json.loads(line)
            event_payload = payload.get("payload", {})
            events.append(
                TraceEvent(
                    event_type=str(payload["event_type"]),
                    stage=str(payload["stage"]),
                    game_id=str(payload["game_id"]),
                    step_idx=int(payload["step_idx"]),
                    payload=dict(event_payload) if isinstance(event_payload, dict) else {},
                    timestamp=str(payload["timestamp"]),
                )
            )
    return events


def _coerce_retry_count(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
