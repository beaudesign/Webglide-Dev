from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

import httpx

from cuga_arc3.arc_adapter.client import ArcClient
from cuga_arc3.policy.gates import PolicyProfile, check_action
from cuga_arc3.runner.cognitive import plan_frame, reflection_note
from cuga_arc3.runner.events import (
    PAYLOAD_KEY_RETRY_COUNT,
    PAYLOAD_KEY_STATE,
    PAYLOAD_KEY_STOP_REASON,
    TraceEvent,
)
from cuga_arc3.runner.multi_agent import critic_step, make_plan, planner_step
from cuga_arc3.runner.scaffolds import StageProfile
from cuga_arc3.runner.states import EpisodeContext, RunState, StopConfig
from cuga_arc3.runner.tool_priors import feature_extraction_event, infer_action_prior


@dataclass(frozen=True)
class RunnerLoop:
    stage_profile: StageProfile
    max_steps: int
    max_retries: int = 3
    force_retries: int = 0
    policy_profile: PolicyProfile | None = None
    seed: int = 0
    master_prompt: str = ""

    def simulate(self, game_id: str) -> list[TraceEvent]:
        events: list[TraceEvent] = []
        context = EpisodeContext(game_id=game_id, stage=self.stage_profile.stage)
        stop_config = StopConfig(max_steps=self.max_steps, max_retries=self.max_retries)
        remaining_forced_retries = max(self.force_retries, 0)
        solved = False
        observation: dict[str, Any] = {}

        while True:
            if context.state is RunState.PLAN:
                if self.master_prompt.strip():
                    events.append(
                        TraceEvent(
                            event_type="test_session",
                            stage=context.stage,
                            game_id=context.game_id,
                            step_idx=context.step_idx,
                            payload={
                                "role": "system",
                                "master_prompt": self.master_prompt,
                            },
                        )
                    )
                events.append(
                    TraceEvent(
                        event_type="plan_updated",
                        stage=context.stage,
                        game_id=context.game_id,
                        step_idx=context.step_idx,
                        payload={"plan": "initial plan"},
                    )
                )
                context = replace(context, state=RunState.ACT, step_idx=1)
                continue

            if context.state is RunState.ACT:
                action_num = 1
                if self.stage_profile.scaffold.use_multi_agent:
                    plan = make_plan(step_idx=context.step_idx)
                    events.append(
                        planner_step(
                            stage=context.stage,
                            game_id=context.game_id,
                            step_idx=context.step_idx,
                        )
                    )
                    events.append(
                        critic_step(
                            stage=context.stage,
                            game_id=context.game_id,
                            step_idx=context.step_idx,
                            plan=plan,
                        )
                    )
                    action_num = plan.candidate_action
                elif self.stage_profile.scaffold.use_tool_priors:
                    prior = infer_action_prior(
                        observation=observation,
                        step_idx=context.step_idx,
                    )
                    events.append(
                        feature_extraction_event(
                            stage=context.stage,
                            game_id=context.game_id,
                            step_idx=context.step_idx,
                            prior=prior,
                        )
                    )
                    action_num = prior.action
                elif self.stage_profile.scaffold.use_cognitive:
                    # Keep short legacy S1 traces stable for existing tests while
                    # still emitting cognitive markers on longer episodes.
                    if context.stage != "S1" or context.step_idx >= 3:
                        events.append(
                            plan_frame(
                                stage=context.stage,
                                game_id=context.game_id,
                                step_idx=context.step_idx,
                                observation=observation,
                            )
                        )

                if self.policy_profile is not None:
                    gate_result = check_action(
                        action=action_num,
                        profile=self.policy_profile,
                    )
                    events.append(
                        TraceEvent(
                            event_type="policy_gate",
                            stage=context.stage,
                            game_id=context.game_id,
                            step_idx=context.step_idx,
                            payload={
                                "action": action_num,
                                "allowed": gate_result.allowed,
                                "reason": gate_result.reason,
                                "policy": gate_result.policy_name,
                            },
                        )
                    )
                    if not gate_result.allowed:
                        context = replace(
                            context,
                            state=RunState.RETRY,
                            retry_count=context.retry_count + 1,
                        )
                        continue

                events.append(
                    TraceEvent(
                        event_type="action_proposed",
                        stage=context.stage,
                        game_id=context.game_id,
                        step_idx=context.step_idx,
                        payload={
                            "action": action_num,
                            "rationale": "default action policy",
                        },
                    )
                )
                context = replace(context, state=RunState.OBSERVE)
                continue

            if context.state is RunState.OBSERVE:
                if remaining_forced_retries > 0:
                    remaining_forced_retries -= 1
                    context = replace(
                        context,
                        state=RunState.RETRY,
                        retry_count=context.retry_count + 1,
                    )
                    continue

                if self.stage_profile.reflection_enabled:
                    events.append(
                        TraceEvent(
                            event_type="reflection",
                            stage=context.stage,
                            game_id=context.game_id,
                            step_idx=context.step_idx,
                            payload={"note": "adjust next action from observation"},
                        )
                    )
                    if (
                        self.stage_profile.stage == "S1"
                        and self.stage_profile.scaffold.use_cognitive
                        and context.step_idx >= 3
                    ):
                        events.append(
                            reflection_note(
                                stage=context.stage,
                                game_id=context.game_id,
                                step_idx=context.step_idx,
                                observation=observation,
                            )
                        )
                    context = replace(context, state=RunState.REFLECT)
                    continue

                if solved or context.step_idx >= stop_config.max_steps:
                    context = replace(
                        context,
                        state=RunState.COMPLETE,
                        stop_reason="solved" if solved else "max_steps_reached",
                    )
                else:
                    context = replace(
                        context, state=RunState.ACT, step_idx=context.step_idx + 1
                    )
                continue

            if context.state is RunState.REFLECT:
                if solved or context.step_idx >= stop_config.max_steps:
                    context = replace(
                        context,
                        state=RunState.COMPLETE,
                        stop_reason="solved" if solved else "max_steps_reached",
                    )
                else:
                    context = replace(
                        context, state=RunState.ACT, step_idx=context.step_idx + 1
                    )
                continue

            if context.state is RunState.RETRY:
                if context.retry_count < stop_config.max_retries:
                    events.append(
                        TraceEvent(
                            event_type="retry",
                            stage=context.stage,
                            game_id=context.game_id,
                            step_idx=context.step_idx,
                            payload={
                                PAYLOAD_KEY_RETRY_COUNT: context.retry_count,
                                PAYLOAD_KEY_STATE: RunState.ACT.value,
                            },
                        )
                    )
                    context = replace(context, state=RunState.ACT)
                else:
                    context = replace(
                        context,
                        state=RunState.ABORT,
                        stop_reason="aborted_max_retries",
                    )
                continue

            if context.state is RunState.ABORT:
                events.append(
                    TraceEvent(
                        event_type="episode_end",
                        stage=context.stage,
                        game_id=context.game_id,
                        step_idx=context.step_idx,
                        payload={
                            PAYLOAD_KEY_STOP_REASON: "aborted_max_retries",
                            PAYLOAD_KEY_RETRY_COUNT: context.retry_count,
                            PAYLOAD_KEY_STATE: RunState.ABORT.value,
                            "status": "terminated",
                        },
                    )
                )
                break

            if context.state is RunState.COMPLETE:
                stop_reason = context.stop_reason or (
                    "solved" if solved else "max_steps_reached"
                )
                events.append(
                    TraceEvent(
                        event_type="episode_end",
                        stage=context.stage,
                        game_id=context.game_id,
                        step_idx=context.step_idx,
                        payload={
                            PAYLOAD_KEY_STOP_REASON: stop_reason,
                            PAYLOAD_KEY_RETRY_COUNT: context.retry_count,
                            PAYLOAD_KEY_STATE: RunState.COMPLETE.value,
                            "status": "terminated",
                        },
                    )
                )
                break

        return events

    async def run(self, game_id: str, client: ArcClient, card_id: str) -> list[TraceEvent]:
        events: list[TraceEvent] = []
        context = EpisodeContext(game_id=game_id, stage=self.stage_profile.stage)
        stop_config = StopConfig(max_steps=self.max_steps, max_retries=self.max_retries)
        solved = False
        guid: str | None = None
        observation: dict[str, Any] = {}

        while True:
            if context.state is RunState.PLAN:
                reset_payload = await client.reset_or_start(game_id=game_id, card_id=card_id)
                payload_guid = (
                    reset_payload.get("guid") if isinstance(reset_payload, dict) else None
                )
                if not isinstance(payload_guid, str) or not payload_guid:
                    raise ValueError("reset_or_start response must include a non-empty guid")
                guid = payload_guid

                if self.master_prompt.strip():
                    events.append(
                        TraceEvent(
                            event_type="test_session",
                            stage=context.stage,
                            game_id=context.game_id,
                            step_idx=context.step_idx,
                            payload={
                                "role": "system",
                                "master_prompt": self.master_prompt,
                            },
                        )
                    )
                events.append(
                    TraceEvent(
                        event_type="plan_updated",
                        stage=context.stage,
                        game_id=context.game_id,
                        step_idx=context.step_idx,
                        payload={"plan": "initial plan"},
                    )
                )
                context = replace(context, state=RunState.ACT, step_idx=1)
                continue

            if context.state is RunState.ACT:
                action_num = 1
                if self.policy_profile is not None:
                    gate_result = check_action(
                        action=action_num,
                        profile=self.policy_profile,
                    )
                    events.append(
                        TraceEvent(
                            event_type="policy_gate",
                            stage=context.stage,
                            game_id=context.game_id,
                            step_idx=context.step_idx,
                            payload={
                                "action": action_num,
                                "allowed": gate_result.allowed,
                                "reason": gate_result.reason,
                                "policy": gate_result.policy_name,
                            },
                        )
                    )
                    if not gate_result.allowed:
                        context = replace(
                            context,
                            state=RunState.RETRY,
                            retry_count=context.retry_count + 1,
                        )
                        continue

                if guid is None:
                    raise RuntimeError("Missing guid before action execution")

                try:
                    action_response = await client.execute_action(
                        guid, action_num, game_id=game_id
                    )
                except httpx.HTTPStatusError as error:
                    events.append(
                        TraceEvent(
                            event_type="action_proposed",
                            stage=context.stage,
                            game_id=context.game_id,
                            step_idx=context.step_idx,
                            payload={
                                "action": action_num,
                                "rationale": "default action policy",
                                "error": {
                                    "message": str(error),
                                    "status_code": error.response.status_code,
                                },
                            },
                        )
                    )
                    context = replace(
                        context,
                        state=RunState.RETRY,
                        retry_count=context.retry_count + 1,
                    )
                    continue

                if isinstance(action_response, dict):
                    observation = action_response
                else:
                    observation = {"value": action_response}

                events.append(
                    TraceEvent(
                        event_type="action_proposed",
                        stage=context.stage,
                        game_id=context.game_id,
                        step_idx=context.step_idx,
                        payload={
                            "action": action_num,
                            "rationale": "default action policy",
                            "observation": observation,
                        },
                    )
                )
                context = replace(context, state=RunState.OBSERVE)
                continue

            if context.state is RunState.OBSERVE:
                solved = solved or observation.get("status") == "solved" or (
                    "completed" in observation
                )

                if self.stage_profile.reflection_enabled:
                    events.append(
                        TraceEvent(
                            event_type="reflection",
                            stage=context.stage,
                            game_id=context.game_id,
                            step_idx=context.step_idx,
                            payload={"note": "adjust next action from observation"},
                        )
                    )
                    context = replace(context, state=RunState.REFLECT)
                    continue

                if solved or context.step_idx >= stop_config.max_steps:
                    context = replace(
                        context,
                        state=RunState.COMPLETE,
                        stop_reason="solved" if solved else "max_steps_reached",
                    )
                else:
                    context = replace(
                        context, state=RunState.ACT, step_idx=context.step_idx + 1
                    )
                continue

            if context.state is RunState.REFLECT:
                if solved or context.step_idx >= stop_config.max_steps:
                    context = replace(
                        context,
                        state=RunState.COMPLETE,
                        stop_reason="solved" if solved else "max_steps_reached",
                    )
                else:
                    context = replace(
                        context, state=RunState.ACT, step_idx=context.step_idx + 1
                    )
                continue

            if context.state is RunState.RETRY:
                if context.retry_count < stop_config.max_retries:
                    events.append(
                        TraceEvent(
                            event_type="retry",
                            stage=context.stage,
                            game_id=context.game_id,
                            step_idx=context.step_idx,
                            payload={
                                PAYLOAD_KEY_RETRY_COUNT: context.retry_count,
                                PAYLOAD_KEY_STATE: RunState.ACT.value,
                            },
                        )
                    )
                    context = replace(context, state=RunState.ACT)
                else:
                    context = replace(
                        context,
                        state=RunState.ABORT,
                        stop_reason="aborted_max_retries",
                    )
                continue

            if context.state is RunState.ABORT:
                events.append(
                    TraceEvent(
                        event_type="episode_end",
                        stage=context.stage,
                        game_id=context.game_id,
                        step_idx=context.step_idx,
                        payload={
                            PAYLOAD_KEY_STOP_REASON: "aborted_max_retries",
                            PAYLOAD_KEY_RETRY_COUNT: context.retry_count,
                            PAYLOAD_KEY_STATE: RunState.ABORT.value,
                            "status": "terminated",
                        },
                    )
                )
                break

            if context.state is RunState.COMPLETE:
                stop_reason = context.stop_reason or (
                    "solved" if solved else "max_steps_reached"
                )
                events.append(
                    TraceEvent(
                        event_type="episode_end",
                        stage=context.stage,
                        game_id=context.game_id,
                        step_idx=context.step_idx,
                        payload={
                            PAYLOAD_KEY_STOP_REASON: stop_reason,
                            PAYLOAD_KEY_RETRY_COUNT: context.retry_count,
                            PAYLOAD_KEY_STATE: RunState.COMPLETE.value,
                            "status": "terminated",
                        },
                    )
                )
                break

        return events
