# ADR 0001: Windows-native local web app

- Status: Accepted
- Date: 2026-10-16

## Context

Gracenote needs a GPU for source separation, pitch tracking and speech recognition (RTX 4060 8GB, 32GB RAM, Windows). The UI needs a piano roll, a clickable tab editor and a sample-accurate metronome. It is a single-user tool and a portfolio project.

## Decision

Run the backend (Python, FastAPI) directly on Windows and serve a React + TypeScript frontend in the browser on localhost. Launch with one `start.bat`. Wrap it as an `.exe` with Tauri only later, if wanted.

## Alternatives considered

- WSL2 / Ubuntu for the whole project: easier installs for some music libraries, but adds a layer the user does not want. Kept only as a fallback for a single stage that cannot run on Windows.
- Pure-Python desktop app (PyQt): much harder to build a smooth piano roll and tab editor, and alphaTab cannot be used.
- Hosted web service: needs rented GPUs, and downloading from YouTube on a server raises legal problems.

## Consequences

- Dependencies must install on Windows. Libraries that do not (madmom, essentia, vamp-based tools) are replaced (see ADR 0003).
- Every claim of "works" must be verified on the target machine; the Phase 0 checklist and `scripts/check_env.py` exist for that.
- The backend must bind to 127.0.0.1 only.
