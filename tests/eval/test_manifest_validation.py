from __future__ import annotations

from pathlib import Path

import pytest

from cuga_arc3.eval.manifest import BenchmarkManifest


def test_manifest_requires_50_total_games() -> None:
    manifest = BenchmarkManifest.from_dict(
        {
            "core": [f"core-{idx:02d}" for idx in range(1, 31)],
            "stress": [f"stress-{idx:02d}" for idx in range(1, 21)],
        }
    )

    assert len(manifest.core) == 30
    assert len(manifest.stress) == 20
    assert manifest.total_games == 50


def test_manifest_rejects_duplicate_ids_within_section() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        BenchmarkManifest.from_dict(
            {
                "core": ["dup-core", "dup-core"] + [f"core-{idx:02d}" for idx in range(1, 29)],
                "stress": [f"stress-{idx:02d}" for idx in range(1, 21)],
            }
        )


def test_manifest_rejects_overlap_between_core_and_stress() -> None:
    overlapping_id = "shared-01"
    with pytest.raises(ValueError, match="overlap"):
        BenchmarkManifest.from_dict(
            {
                "core": [overlapping_id] + [f"core-{idx:02d}" for idx in range(1, 30)],
                "stress": [overlapping_id] + [f"stress-{idx:02d}" for idx in range(1, 20)],
            }
        )


def test_manifest_accepts_optional_master_prompt() -> None:
    manifest = BenchmarkManifest.from_dict(
        {
            "core": [f"core-{idx:02d}" for idx in range(1, 31)],
            "stress": [f"stress-{idx:02d}" for idx in range(1, 21)],
            "master_prompt": "You are taking ARC-3.\nBe concise.",
        }
    )

    assert manifest.master_prompt == "You are taking ARC-3.\nBe concise."


def test_manifest_rejects_non_string_master_prompt() -> None:
    with pytest.raises(ValueError, match="master_prompt"):
        BenchmarkManifest.from_dict(
            {
                "core": [f"core-{idx:02d}" for idx in range(1, 31)],
                "stress": [f"stress-{idx:02d}" for idx in range(1, 21)],
                "master_prompt": 42,
            }
        )


def test_manifest_loads_from_yaml_path() -> None:
    manifest_path = (
        Path(__file__).resolve().parents[2]
        / "benchmark"
        / "manifests"
        / "arc3-core30-stress20.yaml"
    )

    manifest = BenchmarkManifest.from_yaml_path(manifest_path)

    assert manifest.total_games == 50
