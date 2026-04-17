from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RunState(str, Enum):
    PLAN = "PLAN"
    ACT = "ACT"
    OBSERVE = "OBSERVE"
    REFLECT = "REFLECT"
    RETRY = "RETRY"
    ABORT = "ABORT"
    COMPLETE = "COMPLETE"


@dataclass(frozen=True)
class EpisodeContext:
    game_id: str
    stage: str
    step_idx: int = 0
    retry_count: int = 0
    stop_reason: str = ""
    state: RunState = RunState.PLAN


@dataclass(frozen=True)
class StopConfig:
    max_steps: int
    max_retries: int = 3
