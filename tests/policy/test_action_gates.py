from __future__ import annotations

from cuga_arc3.policy.gates import (
    PROFILES,
    ApprovalMode,
    PolicyProfile,
    check_action,
)
from cuga_arc3.runner.loop import RunnerLoop
from cuga_arc3.runner.scaffolds import STAGE_PROFILES


def test_arc3_default_allows_all_valid_actions() -> None:
    profile = PROFILES["arc3_default"]

    for action in range(1, 8):
        result = check_action(action=action, profile=profile)
        assert result.allowed is True


def test_browser_conservative_warns_action6() -> None:
    result = check_action(action=6, profile=PROFILES["browser_conservative"])

    assert result.allowed is False
    assert result.reason == "blocked_action"


def test_enterprise_strict_blocks_action6_and_7() -> None:
    profile = PROFILES["enterprise_strict"]

    for action in (6, 7):
        result = check_action(action=action, profile=profile)
        assert result.allowed is False
        assert result.reason == "blocked_action"


def test_enterprise_strict_flags_require_human_for_allowed_action() -> None:
    result = check_action(action=1, profile=PROFILES["enterprise_strict"])

    assert result.allowed is True
    assert result.reason == "require_human"


def test_runner_emits_policy_gate_event() -> None:
    loop = RunnerLoop(
        stage_profile=STAGE_PROFILES["S0"],
        max_steps=1,
        policy_profile=PROFILES["arc3_default"],
    )

    events = loop.simulate(game_id="game-policy-gate")

    assert any(event.event_type == "policy_gate" for event in events)


def test_blocked_action_triggers_retry() -> None:
    loop = RunnerLoop(
        stage_profile=STAGE_PROFILES["S0"],
        max_steps=1,
        policy_profile=PolicyProfile(
            name="block_default_action",
            allowed_actions=None,
            blocked_actions=frozenset({1}),
            approval_mode=ApprovalMode.AUTO,
        ),
    )

    events = loop.simulate(game_id="game-policy-retry")

    assert any(event.event_type == "retry" for event in events)
