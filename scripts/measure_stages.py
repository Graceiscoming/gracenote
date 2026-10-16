"""Phase 0: measure wall time and peak VRAM of each GPU stage on one song.

    python scripts/measure_stages.py samples/sample1.mp3 --out <scratch dir>

Every stage runs in its own subprocess so VRAM is fully released between stages (as in the
real pipeline). The parent samples GPU memory through NVML every 50 ms and reports the peak
above the idle baseline. Results are printed as a Markdown table for docs/PHASE0_REPORT.md.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import threading
import time
from pathlib import Path

import pynvml

ROOT = Path(__file__).resolve().parents[1]
POLL_SECONDS = 0.05
MIB = 1024 * 1024


def _used_mib(handle: object) -> float:
    return pynvml.nvmlDeviceGetMemoryInfo(handle).used / MIB


def run_measured(cmd: list[str]) -> tuple[float, float, int]:
    """Run ``cmd``; return (wall seconds, peak VRAM above baseline in MiB, exit code)."""
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    baseline = _used_mib(handle)
    peak = baseline
    stop = threading.Event()

    def poll() -> None:
        nonlocal peak
        while not stop.is_set():
            peak = max(peak, _used_mib(handle))
            time.sleep(POLL_SECONDS)

    thread = threading.Thread(target=poll, daemon=True)
    thread.start()
    start = time.perf_counter()
    code = subprocess.run(cmd, check=False).returncode
    wall = time.perf_counter() - start
    stop.set()
    thread.join()
    return wall, peak - baseline, code


def worker_f0(vocals: Path) -> None:
    import soundfile as sf
    import torch
    import torchcrepe

    samples, sr = sf.read(str(vocals), dtype="float32", always_2d=True)
    audio = torch.from_numpy(samples.mean(axis=1))[None]
    torchcrepe.predict(
        audio, sr, hop_length=sr // 100, fmin=50, fmax=1100, model="full",
        batch_size=512, device="cuda:0",
    )  # fmt: skip
    torch.cuda.synchronize()


def worker_whisper(vocals: Path) -> None:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.windows_dll import add_nvidia_dll_dirs

    add_nvidia_dll_dirs()
    from faster_whisper import WhisperModel

    model = WhisperModel("large-v3", device="cuda", compute_type="float16")
    segments, info = model.transcribe(str(vocals), word_timestamps=True)
    words = sum(len(s.words or []) for s in segments)
    print(f"whisper language={info.language} words={words}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("song", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="scratch folder for stems")
    parser.add_argument("--worker", choices=["f0", "whisper"], help=argparse.SUPPRESS)
    parser.add_argument("--vocals", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.worker == "f0":
        worker_f0(args.vocals)
        return 0
    if args.worker == "whisper":
        worker_whisper(args.vocals)
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    py = sys.executable
    me = str(Path(__file__).resolve())
    vocals = args.out / "htdemucs" / args.song.stem / "vocals.wav"
    stages = {
        "Separation (htdemucs, vocals only)": [
            py, "-m", "demucs", "--two-stems=vocals", "-d", "cuda", "-o", str(args.out),
            str(args.song),
        ],
        "F0 (torchcrepe full)": [py, me, str(args.song), "--out", str(args.out),
                                 "--worker", "f0", "--vocals", str(vocals)],
        "Lyrics (faster-whisper large-v3 fp16)": [
            py, me, str(args.song), "--out", str(args.out), "--worker", "whisper",
            "--vocals", str(vocals),
        ],
    }  # fmt: skip
    print("| Stage | Wall time (s) | Peak VRAM (MiB) | Exit |\n|---|---|---|---|")
    failed = False
    for name, cmd in stages.items():
        wall, peak, code = run_measured(cmd)
        failed |= code != 0
        print(f"| {name} | {wall:.1f} | {peak:.0f} | {code} |", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
