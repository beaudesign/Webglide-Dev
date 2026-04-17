from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScaffoldStrategy:
    use_cognitive: bool = False
    use_tool_priors: bool = False
    use_multi_agent: bool = False


@dataclass(frozen=True)
class StageProfile:
    stage: str
    scaffold: ScaffoldStrategy = field(default_factory=ScaffoldStrategy)

    @property
    def reflection_enabled(self) -> bool:
        return self.scaffold.use_cognitive

    @property
    def tool_priors_enabled(self) -> bool:
        return self.scaffold.use_tool_priors

    @property
    def multi_agent_enabled(self) -> bool:
        return self.scaffold.use_multi_agent


STAGE_PROFILES: dict[str, StageProfile] = {
    "S0": StageProfile(
        stage="S0",
        scaffold=ScaffoldStrategy(),
    ),
    "S1": StageProfile(
        stage="S1",
        scaffold=ScaffoldStrategy(
            use_cognitive=True,
        ),
    ),
    "S2": StageProfile(
        stage="S2",
        scaffold=ScaffoldStrategy(
            use_cognitive=True,
            use_tool_priors=True,
        ),
    ),
    "S3": StageProfile(
        stage="S3",
        scaffold=ScaffoldStrategy(
            use_cognitive=True,
            use_tool_priors=True,
            use_multi_agent=True,
        ),
    ),
}
