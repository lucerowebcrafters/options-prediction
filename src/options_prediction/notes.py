from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Iterable, List


def load_notes(path: Path) -> List[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_notes(path: Path, notes: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for note in notes:
            handle.write(f"[{dt.datetime.utcnow().isoformat()}] {note}\n")


def record_iteration_summary(path: Path, summary: str) -> None:
    append_notes(path, [summary])
