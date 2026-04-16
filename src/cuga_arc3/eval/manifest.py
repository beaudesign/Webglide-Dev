from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CORE_BENCHMARK_COUNT = 30
STRESS_BENCHMARK_COUNT = 20


@dataclass(frozen=True)
class BenchmarkManifest:
    core: tuple[str, ...]
    stress: tuple[str, ...]

    @property
    def total_games(self) -> int:
        return len(self.core) + len(self.stress)

    @classmethod
    def from_dict(cls, raw_manifest: dict[str, Any]) -> "BenchmarkManifest":
        if not isinstance(raw_manifest, dict):
            raise ValueError("manifest must be a dictionary")

        core = cls._validate_game_ids(
            raw_manifest.get("core"), section="core", expected_count=CORE_BENCHMARK_COUNT
        )
        stress = cls._validate_game_ids(
            raw_manifest.get("stress"),
            section="stress",
            expected_count=STRESS_BENCHMARK_COUNT,
        )
        return cls(core=core, stress=stress)

    @staticmethod
    def _validate_game_ids(
        game_ids: Any, *, section: str, expected_count: int
    ) -> tuple[str, ...]:
        if not isinstance(game_ids, list):
            raise ValueError(f"manifest section '{section}' must be a list of game ids")

        if len(game_ids) != expected_count:
            raise ValueError(
                f"manifest section '{section}' must contain exactly {expected_count} game ids"
            )

        if any(not isinstance(game_id, str) or not game_id.strip() for game_id in game_ids):
            raise ValueError(
                f"manifest section '{section}' must only contain non-empty string game ids"
            )

        return tuple(game_ids)
