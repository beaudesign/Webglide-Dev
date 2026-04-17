from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ARTIFACT_VERSION = "1.0"


@dataclass(frozen=True)
class RunArtifact:
    run_id: str
    stage: str
    manifest_path: str
    total_games: int
    created_at: str
    stages: list[dict[str, Any]]
    lifts: list[dict[str, Any]]
    game_traces: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    artifact_version: str = ARTIFACT_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "artifact_version": self.artifact_version,
            "run_id": self.run_id,
            "stage": self.stage,
            "manifest_path": self.manifest_path,
            "total_games": self.total_games,
            "created_at": self.created_at,
            "stages": self.stages,
            "lifts": self.lifts,
            "game_traces": self.game_traces,
            "summary": self.summary,
        }
        # Backwards-compatible aliases preserved for existing consumers.
        if self.game_traces:
            payload["processed_game_ids"] = [
                trace["game_id"]
                for trace in self.game_traces
                if isinstance(trace, dict) and isinstance(trace.get("game_id"), str)
            ]
            payload["total_processed"] = len(payload["processed_game_ids"])
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RunArtifact:
        artifact_version = payload.get("artifact_version")
        if artifact_version != ARTIFACT_VERSION:
            raise ValueError(
                f"Unsupported artifact_version '{artifact_version}', expected '{ARTIFACT_VERSION}'."
            )
        return cls(
            artifact_version=artifact_version,
            run_id=str(payload["run_id"]),
            stage=str(payload["stage"]),
            manifest_path=str(payload["manifest_path"]),
            total_games=int(payload["total_games"]),
            created_at=str(payload["created_at"]),
            stages=list(payload["stages"]),
            lifts=list(payload["lifts"]),
            game_traces=list(payload.get("game_traces", [])),
            summary=dict(payload.get("summary", {})),
        )
