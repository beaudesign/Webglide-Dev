from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StageMetrics:
    stage: str
    wins: int
    total_games: int

    @property
    def win_rate(self) -> float:
        if self.total_games == 0:
            return 0.0
        return self.wins / self.total_games


def compute_stage_metrics(*, stage: str, wins: int, total_games: int) -> StageMetrics:
    if total_games < 0:
        raise ValueError("total_games must be non-negative")
    if wins < 0:
        raise ValueError("wins must be non-negative")
    if wins > total_games:
        raise ValueError("wins cannot exceed total_games")

    return StageMetrics(stage=stage, wins=wins, total_games=total_games)
