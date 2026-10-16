# Phase 0 report

Measured on the target machine (Windows 11, i5-13500HX, RTX 4060 Laptop 8GB, 32GB RAM).
Rows left empty were not measured yet.

## Environment check

Output of `python scripts/check_env.py --deep` (exit code 0):

```
[PASS] Python 3.10/3.11  3.11.9
[PASS] PyTorch + CUDA GPU  NVIDIA GeForce RTX 4060 Laptop GPU, 8.0 GB VRAM, torch 2.14.1+cu126
[PASS] ffmpeg  ...\Gyan.FFmpeg...\ffmpeg-9.0-full_build\bin\ffmpeg.EXE
[PASS] Node.js  C:\Program Files\nodejs\node.EXE
[WARN] rubberband (time-stretch)  not found in PATH | fix: only needed for slow-down / transpose backing track (Phase 7)
[PASS] FastAPI  0.143.2
[PASS] uvicorn  0.54.0
[PASS] pydantic  2.14.1
[PASS] psutil  7.2.2
[PASS] nvidia-ml-py (pynvml)
[PASS] yt-dlp
[PASS] soundfile  0.14.0
[PASS] numpy  2.4.6
[PASS] scipy  1.17.1
[PASS] librosa  0.11.0
[PASS] demucs  4.1.0
[PASS] audio-separator
[PASS] torchcrepe
[PASS] faster-whisper  1.2.1
[PASS] PyThaiNLP  5.4.0
[PASS] music21  10.5.0
[PASS] Playwright
[PASS] mir_eval  0.8.2
[PASS] beat_this (beat/downbeat)
[PASS] faster-whisper CUDA (ctranslate2)  1 CUDA device(s) visible; this does not prove cuDNN/cuBLAS load, run with --deep for a real transcription
[PASS] pyrubberband  0.4.0
[PASS] faster-whisper real transcription on GPU (--deep)  tiny model ran on CUDA with float16
[INFO] BTC chord model  manual: clone the BTC repo and download its weights (Phase 0)
[INFO] RMVPE weights  manual: download the RMVPE weights file (Phase 0)
[INFO] Playwright Chromium  run `python -m playwright install chromium` if not done by setup_windows.bat

All required checks passed.
```

## Measured stage cost

Test song: `samples/sample1.mp3`, 316.8 s (about 5 min 17 s), Thai vocals (Whisper detected `th`).
Measured with `python scripts/measure_stages.py samples/sample1.mp3 --out <scratch>`: one subprocess
per stage, peak VRAM sampled through NVML every 50 ms, reported above the idle baseline.
The first full run gives the numbers below. A second run (taken when RMVPE was added) gave 12.6 s / 963 MiB for separation, 27.7 s / 1751 MiB for CREPE and 95.6 s / 5445 MiB for Whisper, so timings vary by roughly 10-30% between runs; VRAM is stable. RMVPE was measured once.

| Stage | Model | Wall time | Peak VRAM | Notes |
|---|---|---|---|---|
| Ingest | yt-dlp + ffmpeg | | | not measured |
| Separation | htdemucs, `--two-stems=vocals` | 12.2 s | 963 MiB | whole subprocess, includes model load |
| F0 | RMVPE (RVC `rmvpe.pt`, fp16) | 9.1 s | 1971 MiB | on the demucs vocals stem; 31685 frames, 22293 voiced; includes loading audio at 16 kHz |
| F0 | CREPE (torchcrepe `full`, 10 ms hop, batch 512) | 38.6 s | 1753 MiB | on the demucs vocals stem |
| Lyrics | faster-whisper large-v3, float16, word timestamps | 79.8 s | 5446 MiB | whole subprocess, includes loading the cached model; 1038 words |
| Beat | beat_this | | | not measured |
| Chords | BTC | | | not measured |

A first run of the lyrics stage took 87.6 s (1015 words); that run may have included model
download time, so the 79.8 s figure above is the one to use. The separation, CREPE and Whisper
stages run one after another and each stays under the 8 GB budget, so the sequential-GPU rule fits.

## Install problems and decisions

| Library | Problem | Decision |
|---|---|---|
| torchcrepe | `torchcrepe.load.audio` calls `torchaudio.load`, which needs `torchcodec` (not installed) | Load audio with `soundfile` and pass a tensor to `torchcrepe.predict`; no new dependency |
| RMVPE | No pip package or official release found; the official-code repo (Dream-High/RMVPE) was not checked | Weights `rmvpe.pt` (181184272 bytes) downloaded from the RVC project's Hugging Face repo `lj1995/VoiceConversionWebUI` into `models/` (git-ignored); sha256 `6d62215f...ec193` matches the LFS hash Hugging Face reports. Model code is RVC's MIT-licensed `infer/rmvpe.py`, kept outside the repo and loaded by `scripts/measure_stages.py --rmvpe-code`; Phase 1 needs its own clean implementation (ADR) |
| rubberband | binary not in PATH (WARN) | Only needed for Phase 7; left as is |
