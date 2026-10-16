# ADR 0003: Use Windows-friendly libraries for beat, key, chord and structure

- Status: Accepted (to be confirmed by the Phase 0 install checklist)
- Date: 2026-10-16

## Context

madmom, essentia, Chordino/vamp and all-in-one (allin1) are common choices for beat tracking, key detection, chords and song structure, but they are hard or impossible to install natively on Windows (compilers, missing wheels, plugin hosts, dependencies on madmom/natten).

## Decision

- Beat / downbeat: `beat_this` (PyTorch) with librosa as a fallback
- Key: chroma from librosa plus several key profiles (Krumhansl, Temperley, Edma) voting, written in-house
- Chords: BTC (PyTorch) as the main model, chroma + template + HMM/Viterbi in-house as a fallback. The audio fed to the chord model (instrumental stem, original mix, or both) is chosen by benchmark, not assumed.
- Autochord is rejected: it is a TensorFlow Bi-LSTM-CRF that needs the Vamp NNLS-Chroma plugin, knows only 25 classes (major, minor, no-chord) and its last release is from October 2021.
- Structure: self-similarity matrix segmentation with librosa, with manual markers in the UI
- Theory layer: music21 for spelling, scales, transposition and key cross-checks (never inside the tab solver's inner loop)

## Alternatives considered

- Move everything to WSL2: works for these libraries, but contradicts ADR 0001 and adds setup friction.
- Skip features: loses chord sheet and metronome features the user wants.

## Consequences

- BTC and RMVPE weights are not installed by pip; they are downloaded manually in Phase 0.
- Chord and key accuracy are measured against the user's ground truth, and the best option per stage becomes the default.
- If a chosen library fails the Phase 0 checklist on the target machine, only that stage is replaced (or moved to WSL2 as a last resort).
