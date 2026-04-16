from __future__ import annotations

from dataclasses import dataclass

from cuga_arc3.runner.events import TraceEvent
from cuga_arc3.runner.scaffolds import STAGE_PROFILES, StageProfile


@dataclass(frozen=True)
class RunnerLoop:
    stage: str
    max_steps: int = 1

    def _stage_profile(self) -> StageProfile:
        profile = STAGE_PROFILES.get(self.stage)
        if profile is None:
            raise ValueError(f"Unsupported stage: {self.stage}")
        return profile

    def simulate(self, game_id: str) -> list[TraceEvent]:
        profile = self._stage_profile()
        events: list[TraceEvent] = [
            TraceEvent(
                event_type="plan_updated",
                stage=self.stage,
                game_id=game_id,
                step_idx=0,
                payload={"max_steps": self.max_steps},
            )
        ]

        for step_idx in range(self.max_steps):
            events.append(
                TraceEvent(
                    event_type="action_proposed",
                    stage=self.stage,
                    game_id=game_id,
                    step_idx=step_idx,
                    payload={"action": (step_idx % 6) + 1},
                )
            )
            if profile.reflection:
                events.append(
                    TraceEvent(
                        event_type="reflection",
                        stage=self.stage,
                        game_id=game_id,
                        step_idx=step_idx,
                        payload={"reflection": f"step_{step_idx}"},
                    )
                )

        events.append(
            TraceEvent(
                event_type="episode_end",
                stage=self.stage,
                game_id=game_id,
                step_idx=self.max_steps,
                payload={"steps_executed": self.max_steps},
            )
        )
        return events
