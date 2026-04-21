from __future__ import annotations

import json
from pathlib import Path

from cuga_arc3.watch_http import build_snapshot_payload


def test_build_snapshot_missing_file(tmp_path: Path) -> None:
    out = build_snapshot_payload(tmp_path / "nope.json")
    assert out["ok"] is False


def test_build_snapshot_splits_events_by_game(tmp_path: Path) -> None:
    artifact = {
        "artifact_version": "1.0",
        "run_id": "r1",
        "stage": "S0",
        "manifest_path": "m.yaml",
        "total_games": 2,
        "created_at": "2026-01-01T00:00:00Z",
        "stages": [],
        "lifts": [],
        "summary": {"master_prompt": "from summary"},
        "game_traces": [
            {
                "game_id": "g1",
                "events": [
                    {"event_type": "plan_updated", "stage": "S0", "game_id": "g1", "step_idx": 0, "payload": {}},
                ],
            },
            {
                "game_id": "g2",
                "events": [
                    {"event_type": "episode_end", "stage": "S0", "game_id": "g2", "step_idx": 1, "payload": {"stop_reason": "solved"}},
                ],
            },
        ],
    }
    path = tmp_path / "run.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    full = build_snapshot_payload(path, game_id=None)
    assert full["ok"] is True
    assert full["game_ids"] == ["g1", "g2"]
    assert full["selected_game_id"] == "g1"
    assert full["master_prompt"] == "from summary"
    assert len(full["events"]) == 1
    assert full["events"][0]["event_type"] == "plan_updated"

    g2 = build_snapshot_payload(path, game_id="g2")
    assert g2["selected_game_id"] == "g2"
    assert len(g2["events"]) == 1
    assert g2["events"][0]["event_type"] == "episode_end"


def test_master_prompt_from_test_session(tmp_path: Path) -> None:
    artifact = {
        "artifact_version": "1.0",
        "run_id": "r1",
        "stage": "S0",
        "manifest_path": "m.yaml",
        "total_games": 1,
        "created_at": "2026-01-01T00:00:00Z",
        "stages": [],
        "lifts": [],
        "summary": {},
        "game_traces": [
            {
                "game_id": "g1",
                "events": [
                    {
                        "event_type": "test_session",
                        "stage": "S0",
                        "game_id": "g1",
                        "step_idx": 0,
                        "payload": {"master_prompt": "hello", "role": "system"},
                    },
                ],
            },
        ],
    }
    path = tmp_path / "run.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    out = build_snapshot_payload(path)
    assert out["master_prompt"] == "hello"
