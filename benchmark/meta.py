"""Sidecar metadata for an exported ground-truth CSV (``<song>.meta.json``)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from label_config import PROVENANCE


@dataclass(frozen=True)
class GroundTruthMeta:
    song: str
    verified_start_sec: float
    verified_end_sec: float
    note_count: int
    provenance: str = PROVENANCE

    def __post_init__(self) -> None:
        if self.verified_end_sec <= self.verified_start_sec:
            raise ValueError("verified_end_sec must be greater than verified_start_sec")


def write_meta(path: Path, meta: GroundTruthMeta) -> None:
    path.write_text(json.dumps(asdict(meta), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_meta(path: Path) -> GroundTruthMeta:
    return GroundTruthMeta(**json.loads(path.read_text(encoding="utf-8")))
