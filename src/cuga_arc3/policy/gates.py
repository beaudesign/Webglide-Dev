from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ApprovalMode(StrEnum):
    AUTO = "auto"
    WARN = "warn"
    REQUIRE_HUMAN = "require_human"


@dataclass(frozen=True)
class PolicyProfile:
    name: str
    allowed_actions: frozenset[int] | None
    blocked_actions: frozenset[int]
    approval_mode: ApprovalMode = ApprovalMode.AUTO


PROFILES: dict[str, PolicyProfile] = {
    "arc3_default": PolicyProfile(
        name="arc3_default",
        allowed_actions=frozenset({1, 2, 3, 4, 5, 6, 7}),
        blocked_actions=frozenset(),
        approval_mode=ApprovalMode.AUTO,
    ),
    "browser_conservative": PolicyProfile(
        name="browser_conservative",
        allowed_actions=None,
        blocked_actions=frozenset({6}),
        approval_mode=ApprovalMode.WARN,
    ),
    "enterprise_strict": PolicyProfile(
        name="enterprise_strict",
        allowed_actions=frozenset({1, 2, 3, 4, 5}),
        blocked_actions=frozenset({6, 7}),
        approval_mode=ApprovalMode.REQUIRE_HUMAN,
    ),
}


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    action: int
    policy_name: str
    reason: str
    approval_mode: ApprovalMode


def check_action(action: int, profile: PolicyProfile) -> GateResult:
    if action in profile.blocked_actions:
        return GateResult(
            allowed=False,
            action=action,
            policy_name=profile.name,
            reason="blocked_action",
            approval_mode=profile.approval_mode,
        )

    if profile.allowed_actions is not None and action not in profile.allowed_actions:
        return GateResult(
            allowed=False,
            action=action,
            policy_name=profile.name,
            reason="not_in_allowlist",
            approval_mode=profile.approval_mode,
        )

    if profile.approval_mode is ApprovalMode.REQUIRE_HUMAN:
        return GateResult(
            allowed=True,
            action=action,
            policy_name=profile.name,
            reason="require_human",
            approval_mode=profile.approval_mode,
        )

    return GateResult(
        allowed=True,
        action=action,
        policy_name=profile.name,
        reason="allowed",
        approval_mode=profile.approval_mode,
    )
