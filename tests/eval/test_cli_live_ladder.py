from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

from cuga_arc3.arc_adapter.client import ArcClient
from cuga_arc3.cli import main
from cuga_arc3.runner.events import TraceEvent
from cuga_arc3.runner.loop import RunnerLoop


def test_live_ladder_uses_client_and_scorecard(
    tmp_path: Path, monkeypatch
) -> None:
    output_path = tmp_path / "ladder-live.json"
    manifest_path = (
        Path(__file__).resolve().parents[2]
        / "benchmark"
        / "manifests"
        / "arc3-core30-stress20.yaml"
    )

    monkeypatch.setenv("ARC_API_KEY", "test-api-key")

    open_scorecard = AsyncMock(
        side_effect=lambda metadata: {"card_id": f"card-{metadata['stage']}"}
    )
    close_scorecard = AsyncMock(
        side_effect=lambda card_id: {"card_id": card_id, "status": "closed"}
    )
    run = AsyncMock(
        side_effect=lambda game_id, client, card_id: [
            TraceEvent(
                event_type="episode_end",
                stage="S0",
                game_id=game_id,
                step_idx=1,
                payload={"stop_reason": "solved", "status": "terminated"},
            )
        ]
    )
    monkeypatch.setattr(ArcClient, "open_scorecard", open_scorecard)
    monkeypatch.setattr(ArcClient, "close_scorecard", close_scorecard)
    monkeypatch.setattr(RunnerLoop, "run", run)

    main(
        [
            "run-ladder",
            "--live",
            "--out",
            str(output_path),
            "--manifest",
            str(manifest_path),
        ]
    )

    assert open_scorecard.await_count == 4
    assert close_scorecard.await_count == 4

    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(report["stages"]) == 4
    assert all("card_id" in stage for stage in report["stages"])
