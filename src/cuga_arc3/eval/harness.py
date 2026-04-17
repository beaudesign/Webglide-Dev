from __future__ import annotations

from dataclasses import dataclass

from cuga_arc3.eval.manifest import BenchmarkManifest
from cuga_arc3.runner.events import PAYLOAD_KEY_RETRY_COUNT, PAYLOAD_KEY_STOP_REASON


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


@dataclass(frozen=True)
class ReliabilityMetrics:
    stage: str
    total_episodes: int
    abort_count: int
    retry_total: int
    invalid_action_count: int

    @property
    def abort_rate(self) -> float:
        if self.total_episodes == 0:
            return 0.0
        return self.abort_count / self.total_episodes

    @property
    def mean_retries(self) -> float:
        if self.total_episodes == 0:
            return 0.0
        return self.retry_total / self.total_episodes


def compute_stage_metrics(
    stage: str, solved_game_ids: list[str], manifest: BenchmarkManifest
) -> StageMetrics:
    manifest_ids = set(manifest.core).union(manifest.stress)
    solved_ids = set(solved_game_ids)
    solved_count = len(solved_ids.intersection(manifest_ids))
    total_games = manifest.total_games

    return StageMetrics(stage=stage, solved_count=solved_count, total_games=total_games)


def compute_reliability_metrics(
    stage: str, game_traces: list[dict]
) -> ReliabilityMetrics:
    total_episodes = len(game_traces)
    abort_count = 0
    retry_total = 0
    invalid_action_count = 0

    for trace in game_traces:
        events = trace.get("events", []) if isinstance(trace, dict) else []
        episode_stop_reason: str | None = None
        episode_retry_count: int | None = None
        episode_retry_events = 0

        for event in events:
            if not isinstance(event, dict):
                continue
            event_type = event.get("event_type")
            if event_type == "retry":
                invalid_action_count += 1
                episode_retry_events += 1

            if event_type != "episode_end":
                continue

            payload = event.get("payload", {})
            if not isinstance(payload, dict):
                continue

            stop_reason = payload.get(PAYLOAD_KEY_STOP_REASON)
            if isinstance(stop_reason, str):
                episode_stop_reason = stop_reason

            retry_count = payload.get(PAYLOAD_KEY_RETRY_COUNT)
            if isinstance(retry_count, int):
                episode_retry_count = retry_count

        if episode_stop_reason == "aborted_max_retries":
            abort_count += 1

        retry_total += (
            episode_retry_count
            if episode_retry_count is not None
            else episode_retry_events
        )

    return ReliabilityMetrics(
        stage=stage,
        total_episodes=total_episodes,
        abort_count=abort_count,
        retry_total=retry_total,
        invalid_action_count=invalid_action_count,
    )
