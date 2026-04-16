from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StageProfile:
    reflection: bool
    tool_priors: bool
    multi_agent: bool


STAGE_PROFILES: dict[str, StageProfile] = {
    "S0": StageProfile(reflection=False, tool_priors=False, multi_agent=False),
    "S1": StageProfile(reflection=True, tool_priors=False, multi_agent=False),
    "S2": StageProfile(reflection=True, tool_priors=True, multi_agent=False),
    "S3": StageProfile(reflection=True, tool_priors=True, multi_agent=True),
}
