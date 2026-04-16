from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    arc_api_key: str
    arc_base_url: str = "https://api.arcprize.org"
    default_stage: str = "S0"
    max_steps_per_game: int = 120

    @classmethod
    def from_env(cls) -> "Settings":
        arc_api_key = os.getenv("ARC_API_KEY", "").strip()
        if not arc_api_key:
            raise ValueError("ARC_API_KEY is required")

        return cls(arc_api_key=arc_api_key)
