"""Tunable numbers for the labeling tool. Nothing numeric is hard-coded elsewhere."""

from __future__ import annotations

from dataclasses import dataclass

PROVENANCE = "machine draft, human verified"


@dataclass(frozen=True)
class SegmentationConfig:
    """Settings for turning an F0 track into draft notes (pitch-change segmentation)."""

    hop_sec: float = 0.01  # RMVPE frame hop (160 samples at 16 kHz)
    median_frames: int = 5  # odd window used to smooth the pitch curve inside a voiced run
    max_gap_sec: float = 0.08  # unvoiced gaps up to this length do not end a note
    min_note_sec: float = 0.08  # shorter segments are merged into a neighbour or dropped
    rmvpe_threshold: float = 0.03  # RMVPE salience threshold for voicing


@dataclass(frozen=True)
class EditConfig:
    """Limits used when editing notes."""

    min_note_sec: float = 0.02  # smallest note the editor accepts
    overlap_tolerance_sec: float = 1e-6
    midi_min: int = 0
    midi_max: int = 127
    default_new_note_sec: float = 0.2  # length of a note added by double-click
    csv_decimals: int = 3  # onset/offset precision in the exported CSV


SEGMENTATION = SegmentationConfig()
EDIT = EditConfig()
