# ADR 0004: Note segmentation from multiple signals, lyrics as a soft hint

- Status: Accepted
- Date: 2026-10-16

## Context

RMVPE and CREPE return a continuous F0 contour. They do not say where one note ends and the next begins. When a singer repeats the same pitch ("la-la-la" on C4), the contour is one flat line, so segmentation by pitch stability alone yields one long note instead of three.

Lyrics alignment (word timestamps from faster-whisper or WhisperX) carries syllable timing, but the number of notes is not the number of words: melisma puts several notes on one syllable, and a held syllable can span several notes. faster-whisper returns word-level timestamps, not phonemes, and how precise they are on singing is not yet measured.

## Decision

Segment notes by combining several signals on the vocal stem:

1. energy (RMS) dips between syllables
2. onset strength (spectral flux, librosa)
3. voicing gaps
4. word boundaries from lyrics alignment, used only as a soft hint that raises the chance of a split, never as a rule
5. optionally Basic Pitch onsets, only if it passes the Phase 0 install checklist on Windows

The user can always split and merge notes in the piano roll. The behaviour is tested first with synthetic audio (the same sine pitch three times with energy dips must give three notes), and the benchmark reports onset F1 so the repeated-pitch case is visible.

## Alternatives considered

- Pitch stability only: fails on repeated notes.
- Force one note per word or syllable: wrong for melisma and held notes.
- A learned note-event model only: possible later, but adds a dependency and needs verification on Windows first.

## Consequences

- Segmentation thresholds and signal weights live in config and are tuned with the benchmark.
- Lyrics alignment becomes an input to segmentation, so the order of stages must allow S9 output to feed S6, or S6 must run a second refinement pass after S9.
- Phoneme-level precision is not assumed anywhere.
