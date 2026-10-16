"""Simple pitch-change note segmentation: F0 track (Hz) -> draft notes.

This is a labeling aid, not the product's note segmenter (ADR 0004): it only looks at F0.
Octave errors from the F0 tracker are left as they are for the human to fix.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import median_filter

from label_config import SEGMENTATION, SegmentationConfig
from notes import Note

A4_HZ = 440.0
A4_MIDI = 69


def hz_to_midi(f0: np.ndarray) -> np.ndarray:
    """Convert Hz to fractional MIDI; unvoiced (<= 0) frames become NaN."""
    midi = np.full(f0.shape, np.nan)
    voiced = f0 > 0
    midi[voiced] = A4_MIDI + 12 * np.log2(f0[voiced] / A4_HZ)
    return midi


def _voiced_runs(voiced: np.ndarray, max_gap: int) -> list[tuple[int, int]]:
    """Index ranges [start, end) of voiced frames, bridging unvoiced gaps up to ``max_gap``."""
    runs: list[tuple[int, int]] = []
    start = last = -1
    for i in (int(v) for v in np.flatnonzero(voiced)):
        if start < 0:
            start = last = i
        elif i - last - 1 <= max_gap:
            last = i
        else:
            runs.append((start, last + 1))
            start = last = i
    if start >= 0:
        runs.append((start, last + 1))
    return runs


def _segments(labels: list[int]) -> list[list[int]]:
    """Group equal consecutive labels into [start, end, label] segments."""
    segs: list[list[int]] = []
    for i, label in enumerate(labels):
        if segs and segs[-1][2] == label:
            segs[-1][1] = i + 1
        else:
            segs.append([i, i + 1, label])
    return segs


def _join_equal(segs: list[list[int]]) -> list[list[int]]:
    out: list[list[int]] = []
    for seg in segs:
        if out and out[-1][2] == seg[2]:
            out[-1][1] = seg[1]
        else:
            out.append(list(seg))
    return out


def _absorb_short(segs: list[list[int]], min_frames: int) -> list[list[int]]:
    """Merge the shortest too-short segment into its longer neighbour until none is left."""
    while len(segs) > 1:
        lengths = [s[1] - s[0] for s in segs]
        shortest = min(range(len(segs)), key=lengths.__getitem__)
        if lengths[shortest] >= min_frames:
            break
        neighbours = [i for i in (shortest - 1, shortest + 1) if 0 <= i < len(segs)]
        target = max(neighbours, key=lengths.__getitem__)
        low, high = sorted((shortest, target))
        segs[low : high + 1] = [[segs[low][0], segs[high][1], segs[target][2]]]
        segs = _join_equal(segs)
    return segs


def f0_to_notes(
    f0: np.ndarray, offset_sec: float = 0.0, config: SegmentationConfig = SEGMENTATION
) -> list[Note]:
    """Turn an F0 track (Hz per frame, 0 = unvoiced) into notes with times shifted by offset."""
    midi = hz_to_midi(np.asarray(f0, dtype=float))
    max_gap = round(config.max_gap_sec / config.hop_sec)
    min_frames = max(1, round(config.min_note_sec / config.hop_sec))
    notes: list[Note] = []
    for start, end in _voiced_runs(~np.isnan(midi), max_gap):
        run = midi[start:end].copy()
        gaps = np.isnan(run)
        if gaps.any():  # bridge short unvoiced gaps with interpolated pitch
            idx = np.arange(len(run))
            run[gaps] = np.interp(idx[gaps], idx[~gaps], run[~gaps])
        smooth = median_filter(run, size=config.median_frames, mode="nearest")
        labels = [int(v) for v in np.rint(smooth)]
        for seg_start, seg_end, label in _absorb_short(_segments(labels), min_frames):
            if seg_end - seg_start < min_frames:
                continue
            onset = offset_sec + (start + seg_start) * config.hop_sec
            offset = offset_sec + (start + seg_end) * config.hop_sec
            notes.append(Note(round(onset, 6), round(offset, 6), label))
    return notes
