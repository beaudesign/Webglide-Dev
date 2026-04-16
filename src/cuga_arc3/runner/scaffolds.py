from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StageProfile:
    stage: str
    reflection_enabled: bool
    tool_priors_enabled: bool
    multi_agent_enabled: bool


STAGE_PROFILES: dict[str, StageProfile] = {
    "S0": StageProfile(
        stage="S0",
        reflection_enabled=False,
        tool_priors_enabled=False,
        multi_agent_enabled=False,
    ),
    "S1": StageProfile(
        stage="S1",
        reflection_enabled=True,
        tool_priors_enabled=False,
        multi_agent_enabled=False,
    ),
    "S2": StageProfile(
        stage="S2",
        reflection_enabled=True,
        tool_priors_enabled=True,
        multi_agent_enabled=False,
    ),
    "S3": StageProfile(
        stage="S3",
        reflection_enabled=True,
        tool_priors_enabled=True,
        multi_agent_enabled=True,
    ),
}
