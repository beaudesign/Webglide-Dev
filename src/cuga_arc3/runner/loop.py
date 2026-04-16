from __future__ import annotations

from dataclasses import dataclass

from cuga_arc3.runner.events import TraceEvent
from cuga_arc3.runner.scaffolds import StageProfile


@dataclass(frozen=True)
class RunnerLoop:
    stage_profile: StageProfile
    max_steps: int

    def simulate(self, game_id: str) -> list[TraceEvent]:
        events: list[TraceEvent] = [
            TraceEvent(
                event_type="plan_updated",
                stage=self.stage_profile.stage,
                game_id=game_id,
                step_idx=0,
                payload={"plan": "initial plan"},
            )
        ]

        for step_idx in range(1, self.max_steps + 1):
            events.append(
                TraceEvent(
                    event_type="action_proposed",
                    stage=self.stage_profile.stage,
                    game_id=game_id,
                    step_idx=step_idx,
                    payload={"action": 1, "rationale": "default action policy"},
                )
            )
            if self.stage_profile.reflection_enabled:
                events.append(
                    TraceEvent(
                        event_type="reflection",
                        stage=self.stage_profile.stage,
                        game_id=game_id,
                        step_idx=step_idx,
                        payload={"note": "adjust next action from observation"},
                    )
                )

        events.append(
            TraceEvent(
                event_type="episode_end",
                stage=self.stage_profile.stage,
                game_id=game_id,
                step_idx=self.max_steps,
                payload={"status": "terminated"},
            )
        )
        return events
