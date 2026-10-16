# Phase 0 report

Filled in on the target machine (Windows, i5-13500HX, RTX 4060 8GB, 32GB RAM). Nothing here has been measured yet.

## Environment check

Output of `python scripts/check_env.py`:

```
(paste here)
```

## Measured stage cost

Test song: (title, length, preset). Measured on the target machine, not estimated.

| Stage | Model | Wall time | Peak VRAM | Notes |
|---|---|---|---|---|
| Ingest | yt-dlp + ffmpeg | | | |
| Separation | | | | |
| F0 | RMVPE | | | |
| F0 | CREPE | | | |
| Lyrics | faster-whisper | | | |
| Beat | beat_this | | | |
| Chords | BTC | | | |

## Install problems and decisions

| Library | Problem | Decision |
|---|---|---|
| | | |
