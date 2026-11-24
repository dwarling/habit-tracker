"""Saving and loading habits to a JSON file (R9)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from habits import HabitTracker

DEFAULT_PATH = Path(__file__).resolve().parent / "data" / "habits.json"


def load(path: Path = DEFAULT_PATH) -> HabitTracker:
    """Load habits from ``path``. A missing file means no habits yet.

    A file that exists but can't be read raises ValueError rather than being
    treated as empty, so a damaged file is never silently overwritten.
    """
    path = Path(path)
    if not path.exists():
        return HabitTracker()
    try:
        with path.open(encoding="utf-8") as f:
            return HabitTracker.from_dict(json.load(f))
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
        raise ValueError(f"Could not read saved habits from {path}: {e}") from e


def save(tracker: HabitTracker, path: Path = DEFAULT_PATH) -> None:
    """Write habits to ``path`` atomically (temp file, then rename)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".habits-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(tracker.to_dict(), f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
