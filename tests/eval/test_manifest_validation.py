from __future__ import annotations

from cuga_arc3.eval.manifest import BenchmarkManifest


def test_manifest_total_is_50_for_30_core_plus_20_stress() -> None:
    manifest = BenchmarkManifest.from_dict(
        {
            "core": [f"core-{idx:02d}" for idx in range(1, 31)],
            "stress": [f"stress-{idx:02d}" for idx in range(1, 21)],
        }
    )

    assert len(manifest.core) == 30
    assert len(manifest.stress) == 20
    assert manifest.total_games == 50
