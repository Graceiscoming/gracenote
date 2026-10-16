# Gracenote

[![CI](https://github.com/<your-username>/gracenote/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-username>/gracenote/actions/workflows/ci.yml)

Transcribe a singer's melody from a song, see it as a piano roll with note names, and turn it into a playable guitar tab that stays inside the fretboard blocks you choose. Runs locally on a Windows machine with an NVIDIA GPU.

> **Status: Phase 0 (setup and benchmark).** Nothing below is finished yet. See the roadmap in [plan.md](plan.md).

<!-- TODO: add a demo GIF of the piano roll and tab editor here -->

## Why

Transcribing a vocal line by ear, finding a playable fingering and writing the tab takes a long time. Gracenote automates the slow parts and keeps the player in control: every note is clickable and editable.

## Planned features

| Area | What it does | Status |
|---|---|---|
| Ingest | YouTube link or audio file in | Planned |
| Analysis | Key, BPM, time signature, chords, lyrics, song sections | Planned |
| Melody | Vocal pitch tracking to notes, key-aware, with confidence per note | Planned |
| Piano roll | Notes with name and octave, synced playback | Planned |
| Chord sheet | Chords over lyrics, auto-scroll, click to seek | Planned |
| Metronome | Click that follows the detected beat grid | Planned |
| Guitar tab | Fingering solver, Block Mode, playability engine | Planned |
| Technique hints | Vocal slides, vibrato and bends mapped to guitar techniques | Planned |
| Easy-key finder | Suggests keys, capo and tuning that are easier to play | Planned |
| Tab editor | Click any note and edit it directly, unlimited undo | Planned |
| Export | Sections as PNG, SVG, PDF; MIDI, MusicXML, Guitar Pro | Planned |
| Projects | Autosave and per-stage cache | Planned |

## How it works

```
audio / YouTube
  -> ingest (yt-dlp, ffmpeg)
  -> source separation (vocals / instrumental)
  -> key, beat, chords (instrumental)    F0 tracking -> note segmentation (vocals)
  -> lyrics + alignment
  -> melody (piano roll) -> tab solver (blocks, playability) -> editor -> export
```

Each stage sits behind one interface and is cached by content hash ([ADR 0002](docs/adr/0002-pipeline-stages-behind-one-interface-with-cache.md)).

## Tech stack

Python 3.11, FastAPI, PyTorch (CUDA), Demucs / BS-RoFormer, RMVPE + CREPE, faster-whisper, librosa, music21, beat_this, BTC. React, TypeScript, Vite, PixiJS, alphaTab, Web Audio API.

## Getting started (Windows)

Requirements: Windows 10/11, NVIDIA GPU with a recent driver, Python 3.11, Git, Node.js LTS, ffmpeg.

```bat
git clone https://github.com/<your-username>/gracenote.git
cd gracenote
setup_windows.bat
.venv\Scripts\activate
python scripts\check_env.py
```

`check_env.py` tells you what works on your machine and what to fix. `start.bat` will be added in Phase 1.

## Accuracy

The melody transcriber is measured with [mir_eval](https://github.com/mir-evaluation/mir_eval) against hand-transcribed songs. Results will be published here once the benchmark exists.

| Metric | Result | Dataset |
|---|---|---|
| Note-level F1 (50 ms onset tolerance) | TBD | TBD |

## Project structure

```
backend/      Python backend (API, pipeline, tab solver) - added from Phase 1
frontend/     React app - added from Phase 1
benchmark/    ground truth and evaluation scripts
scripts/      environment check, helper scripts
tests/        unit tests (pytest)
docs/         engineering standards, ADRs, per-phase goals
plan.md       full specification and roadmap
CLAUDE.md     rules for AI-assisted development
```

## Engineering practices

Conventional Commits, trunk-based branches with pull requests, ruff for lint and format, pytest with a `gpu` marker so CI skips heavy tests, ADRs for architecture decisions. Details in [docs/ENGINEERING.md](docs/ENGINEERING.md).

## Legal and fair use

Downloading audio from YouTube can violate YouTube's terms of service and may infringe copyright. Gracenote is built for personal practice on music you are allowed to use. This repository contains no audio, stems or model weights, and you are responsible for how you use the tool.

## License

TBD
