from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CORE_BENCHMARK_COUNT = 30
STRESS_BENCHMARK_COUNT = 20


@dataclass(frozen=True)
class BenchmarkManifest:
    core: list[str]
    stress: list[str]

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

        if set(core).intersection(stress):
            raise ValueError("manifest sections 'core' and 'stress' must not overlap")

        return cls(core=core, stress=stress)

    @classmethod
    def from_yaml_path(cls, path: str | Path) -> "BenchmarkManifest":
        manifest_path = Path(path)
        with manifest_path.open("r", encoding="utf-8") as manifest_file:
            raw_manifest = yaml.safe_load(manifest_file)

        return cls.from_dict(raw_manifest)

    @staticmethod
    def _validate_game_ids(
        game_ids: Any, *, section: str, expected_count: int
    ) -> list[str]:
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

        if len(set(game_ids)) != len(game_ids):
            raise ValueError(f"manifest section '{section}' contains duplicate ids")

        return game_ids
