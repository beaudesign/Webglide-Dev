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
    master_prompt: str | None = None

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

        master_prompt = _parse_optional_master_prompt(raw_manifest.get("master_prompt"))

        return cls(core=core, stress=stress, master_prompt=master_prompt)

    @classmethod
    def from_yaml_path(cls, path: str | Path) -> "BenchmarkManifest":
        manifest_path = Path(path)
        with manifest_path.open("r", encoding="utf-8") as manifest_file:
            raw_manifest = yaml.safe_load(manifest_file)

        return cls.from_dict(raw_manifest)

    @classmethod
    def from_yaml_path_flexible(cls, path: str | Path) -> "BenchmarkManifest":
        """Load any manifest without enforcing fixed 30/20 counts."""
        manifest_path = Path(path)
        with manifest_path.open("r", encoding="utf-8") as manifest_file:
            raw_manifest = yaml.safe_load(manifest_file)

        if not isinstance(raw_manifest, dict):
            raise ValueError("manifest must be a dictionary")
        core = raw_manifest.get("core", [])
        stress = raw_manifest.get("stress", [])
        if not isinstance(core, list) or not isinstance(stress, list):
            raise ValueError("core and stress must be lists")
        all_ids = core + stress
        if len(set(all_ids)) != len(all_ids):
            raise ValueError("manifest contains duplicate game IDs")
        master_prompt = _parse_optional_master_prompt(raw_manifest.get("master_prompt"))
        return cls(core=list(core), stress=list(stress), master_prompt=master_prompt)

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


def _parse_optional_master_prompt(raw: Any) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise ValueError("master_prompt must be a string when provided")
    stripped = raw.strip()
    return stripped if stripped else None
