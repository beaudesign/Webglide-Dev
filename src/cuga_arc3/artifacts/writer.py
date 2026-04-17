from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cuga_arc3.artifacts.schema import RunArtifact


class ArtifactWriter:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def write(self, artifact: RunArtifact, *, include_jsonl: bool = True) -> tuple[Path, Path | None]:
        self._base_dir.mkdir(parents=True, exist_ok=True)
        json_path = self._base_dir / f"{artifact.run_id}.json"
        json_path.write_text(json.dumps(artifact.to_dict(), indent=2), encoding="utf-8")

        jsonl_path: Path | None = None
        if include_jsonl and artifact.game_traces:
            jsonl_path = self._base_dir / f"{artifact.run_id}.jsonl"
            with jsonl_path.open("w", encoding="utf-8") as trace_file:
                for event in _flatten_events(artifact.game_traces):
                    trace_file.write(json.dumps(event) + "\n")

        return json_path, jsonl_path

    def load(self, run_id: str) -> RunArtifact:
        json_path = self._base_dir / f"{run_id}.json"
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        return RunArtifact.from_dict(payload)


def _flatten_events(game_traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for game_trace in game_traces:
        trace_events = game_trace.get("events")
        if not isinstance(trace_events, list):
            continue
        for event in trace_events:
            if isinstance(event, dict):
                events.append(event)
    return events
