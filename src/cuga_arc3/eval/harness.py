from __future__ import annotations

from dataclasses import dataclass

from cuga_arc3.eval.manifest import BenchmarkManifest


@dataclass(frozen=True)
class StageMetrics:
    stage: str
    solved_count: int
    total_games: int

    @property
    def win_rate(self) -> float:
        if self.total_games == 0:
            return 0.0
        return self.solved_count / self.total_games


def compute_stage_metrics(
    stage: str, solved_game_ids: list[str], manifest: BenchmarkManifest
) -> StageMetrics:
    manifest_ids = set(manifest.core).union(manifest.stress)
    solved_ids = set(solved_game_ids)
    solved_count = len(solved_ids.intersection(manifest_ids))
    total_games = manifest.total_games

    return StageMetrics(stage=stage, solved_count=solved_count, total_games=total_games)
