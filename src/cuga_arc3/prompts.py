from __future__ import annotations

import os
from pathlib import Path


def resolve_master_prompt(
    *,
    inline: str | None = None,
    file_path: str | Path | None = None,
    manifest_master_prompt: str | None = None,
) -> str:
    """Resolve the test master prompt (system instruction) for ARC-3 runs.

    Precedence: CLI inline > CLI file > manifest > ARC_TEST_MASTER_PROMPT >
    ARC_TEST_MASTER_PROMPT_FILE > empty.
    """
    if inline is not None and inline.strip():
        return inline.strip()
    if file_path:
        path = Path(file_path).expanduser()
        return path.read_text(encoding="utf-8").strip()
    if manifest_master_prompt is not None and manifest_master_prompt.strip():
        return manifest_master_prompt.strip()

    env_inline = os.getenv("ARC_TEST_MASTER_PROMPT", "").strip()
    if env_inline:
        return env_inline
    env_file = os.getenv("ARC_TEST_MASTER_PROMPT_FILE", "").strip()
    if env_file:
        return Path(env_file).expanduser().read_text(encoding="utf-8").strip()
    return ""
