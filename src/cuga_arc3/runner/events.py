from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

PAYLOAD_KEY_STOP_REASON = "stop_reason"
PAYLOAD_KEY_RETRY_COUNT = "retry_count"
PAYLOAD_KEY_STATE = "state"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class TraceEvent:
    event_type: str
    stage: str
    game_id: str
    step_idx: int
    payload: dict[str, Any]
    timestamp: str = field(default_factory=_utc_timestamp)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "stage": self.stage,
            "game_id": self.game_id,
            "step_idx": self.step_idx,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }
