from __future__ import annotations

from pathlib import Path

from cuga_arc3.prompts import resolve_master_prompt


def test_resolve_prefers_inline_over_manifest(tmp_path: Path) -> None:
    p = tmp_path / "p.txt"
    p.write_text("from-file", encoding="utf-8")
    text = resolve_master_prompt(
        inline="inline-text",
        file_path=p,
        manifest_master_prompt="from-manifest",
    )
    assert text == "inline-text"


def test_resolve_uses_file_when_no_inline(tmp_path: Path) -> None:
    p = tmp_path / "p.txt"
    p.write_text("  hello file  \n", encoding="utf-8")
    text = resolve_master_prompt(
        inline=None,
        file_path=p,
        manifest_master_prompt="manifest",
    )
    assert text == "hello file"


def test_resolve_falls_back_to_manifest(tmp_path: Path) -> None:
    text = resolve_master_prompt(
        inline=None,
        file_path=None,
        manifest_master_prompt="  m  ",
    )
    assert text == "m"
