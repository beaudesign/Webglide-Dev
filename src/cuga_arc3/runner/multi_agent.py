from __future__ import annotations

from dataclasses import dataclass

from cuga_arc3.runner.events import TraceEvent


@dataclass(frozen=True)
class AgentPlan:
    candidate_action: int
    critic_verdict: str
    critic_note: str


def planner_step(stage: str, game_id: str, step_idx: int) -> TraceEvent:
    return TraceEvent(
        event_type="planner_step",
        stage=stage,
        game_id=game_id,
        step_idx=step_idx,
        payload={
            "candidate_action": step_idx % 5 + 1,
            "plan": "S3 planner: generate candidate from abstract goal",
        },
    )


def critic_step(stage: str, game_id: str, step_idx: int, plan: AgentPlan) -> TraceEvent:
    return TraceEvent(
        event_type="critic_step",
        stage=stage,
        game_id=game_id,
        step_idx=step_idx,
        payload={
            "critic_verdict": plan.critic_verdict,
            "critic_note": plan.critic_note,
        },
    )


def make_plan(step_idx: int) -> AgentPlan:
    candidate_action = step_idx % 5 + 1
    if step_idx % 2 == 0:
        return AgentPlan(
            candidate_action=candidate_action,
            critic_verdict="accept",
            critic_note="ready to execute",
        )
    return AgentPlan(
        candidate_action=candidate_action,
        critic_verdict="reject",
        critic_note="retry with alternate",
    )
