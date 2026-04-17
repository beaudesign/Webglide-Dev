from __future__ import annotations

from cuga_arc3.runner.loop import RunnerLoop
from cuga_arc3.runner.scaffolds import STAGE_PROFILES


def test_s0_has_no_reasoning_or_feature_events() -> None:
    loop = RunnerLoop(stage_profile=STAGE_PROFILES["S0"], max_steps=3)

    events = loop.simulate(game_id="game-s0-scaffold")
    event_types = [event.event_type for event in events]

    assert "reasoning_step" not in event_types
    assert "feature_extraction" not in event_types
    assert "planner_step" not in event_types
    assert "critic_step" not in event_types


def test_s1_emits_reasoning_step() -> None:
    loop = RunnerLoop(stage_profile=STAGE_PROFILES["S1"], max_steps=3)

    events = loop.simulate(game_id="game-s1-scaffold")
    event_types = [event.event_type for event in events]

    assert "reasoning_step" in event_types


def test_s2_emits_feature_extraction() -> None:
    loop = RunnerLoop(stage_profile=STAGE_PROFILES["S2"], max_steps=3)

    events = loop.simulate(game_id="game-s2-scaffold")
    event_types = [event.event_type for event in events]

    assert "feature_extraction" in event_types


def test_s3_emits_planner_and_critic() -> None:
    loop = RunnerLoop(stage_profile=STAGE_PROFILES["S3"], max_steps=3)

    events = loop.simulate(game_id="game-s3-scaffold")
    event_types = [event.event_type for event in events]

    assert "planner_step" in event_types
    assert "critic_step" in event_types


def test_s3_action_matches_planner_candidate() -> None:
    loop = RunnerLoop(stage_profile=STAGE_PROFILES["S3"], max_steps=3)

    events = loop.simulate(game_id="game-s3-candidates")
    planner_candidates = [
        event.payload["candidate_action"]
        for event in events
        if event.event_type == "planner_step"
    ]
    proposed_actions = [
        event.payload["action"] for event in events if event.event_type == "action_proposed"
    ]

    assert planner_candidates
    assert len(planner_candidates) == len(proposed_actions)
    assert proposed_actions == planner_candidates
