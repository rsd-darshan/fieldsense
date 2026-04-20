"""I/O helpers for saving experiment artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def save_json(path: str | Path, payload: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
