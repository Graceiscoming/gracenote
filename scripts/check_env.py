"""Phase 0 environment check for Gracenote (Windows + NVIDIA GPU).

Run from the project root with the virtual environment active:

    python scripts/check_env.py           # quick import / GPU / binary checks
    python scripts/check_env.py --deep    # also really transcribe with faster-whisper on the GPU

``--deep`` downloads the small ``tiny`` Whisper model the first time (needs internet). It is
the check that catches missing cuDNN / cuBLAS DLLs, which a plain import cannot detect.

Exit code is 0 when every *required* check passes, 1 otherwise.
Optional and manual items are reported but never fail the run.
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"
INFO = "INFO"

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"

CUDNN_HINT = (
    "fix: CTranslate2 4.5+ needs cuDNN 9: pip install 'nvidia-cudnn-cu12>=9,<10' "
    "nvidia-cublas-cu12, and call app.windows_dll.add_nvidia_dll_dirs() before importing "
    "faster_whisper (PyTorch 2.4+ also bundles cuDNN 9; importing torch first can help)"
)


@dataclass(frozen=True)
class Result:
    name: str
    status: str
    detail: str = ""
    required: bool = True


def prepare_dll_dirs() -> list[Path]:
    """Register pip-installed NVIDIA DLL folders (Windows only). Never raises."""
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
    try:
        from app.windows_dll import add_nvidia_dll_dirs

        return add_nvidia_dll_dirs()
    except Exception:  # the helper must never stop the checks from running
        return []


def check_python() -> Result:
    version = sys.version_info
    text = f"{version.major}.{version.minor}.{version.micro}"
    if (3, 10) <= (version.major, version.minor) <= (3, 11):
        return Result("Python 3.10/3.11", PASS, text)
    return Result(
        "Python 3.10/3.11",
        WARN,
        f"found {text}; the project targets 3.10/3.11 (set PYVER in setup_windows.bat)",
        required=False,
    )


def check_import(name: str, module: str, hint: str = "", required: bool = True) -> Result:
    try:
        loaded = importlib.import_module(module)
    except Exception as exc:  # any import-time failure means the library is unusable
        detail = f"{type(exc).__name__}: {exc}"
        if hint:
            detail += f" | fix: {hint}"
        return Result(name, FAIL if required else WARN, detail, required)
    version = getattr(loaded, "__version__", "")
    return Result(name, PASS, str(version), required)


def check_binary(name: str, executable: str, hint: str, required: bool = True) -> Result:
    path = shutil.which(executable)
    if path:
        return Result(name, PASS, path, required)
    return Result(name, FAIL if required else WARN, f"not found in PATH | fix: {hint}", required)


def check_cuda() -> Result:
    name = "PyTorch + CUDA GPU"
    try:
        import torch
    except Exception as exc:
        return Result(name, FAIL, f"torch not importable: {exc} | fix: rerun setup_windows.bat")
    if not torch.cuda.is_available():
        return Result(
            name,
            FAIL,
            f"torch {torch.__version__} has no CUDA (CPU-only build or driver problem) | "
            "fix: check `nvidia-smi`, then set CUDA_TAG in setup_windows.bat and reinstall torch",
        )
    try:
        device = torch.cuda.get_device_name(0)
        total_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
        tensor = torch.ones(256, 256, device="cuda", dtype=torch.float16)
        torch.cuda.synchronize()
        _ = tensor @ tensor
        torch.cuda.synchronize()
    except Exception as exc:
        return Result(name, FAIL, f"CUDA is visible but a test matmul failed: {exc}")
    return Result(name, PASS, f"{device}, {total_gb:.1f} GB VRAM, torch {torch.__version__}")


def check_ctranslate2_cuda() -> Result:
    name = "faster-whisper CUDA (ctranslate2)"
    try:
        import ctranslate2
    except Exception as exc:
        return Result(name, FAIL, f"ctranslate2 not importable: {exc}")
    count = ctranslate2.get_cuda_device_count()
    if count > 0:
        return Result(
            name,
            PASS,
            f"{count} CUDA device(s) visible; this does not prove cuDNN/cuBLAS load, "
            "run with --deep for a real transcription",
        )
    return Result(name, FAIL, "no CUDA device visible to ctranslate2")


def check_whisper_transcribe() -> Result:
    """Really run the Whisper encoder on the GPU to catch cuDNN / cuBLAS DLL problems."""
    name = "faster-whisper real transcription on GPU (--deep)"
    prepare_dll_dirs()
    try:
        import numpy as np
        from faster_whisper import WhisperModel
    except Exception as exc:
        return Result(name, FAIL, f"faster-whisper not importable: {exc}")
    try:
        model = WhisperModel("tiny", device="cuda", compute_type="float16")
        audio = np.random.default_rng(0).normal(0, 0.01, 16000).astype(np.float32)
        segments, _ = model.transcribe(audio, language="en")
        list(segments)  # transcription is lazy: consuming the generator runs the model
    except Exception as exc:
        return Result(name, FAIL, f"{type(exc).__name__}: {exc} | {CUDNN_HINT}")
    return Result(name, PASS, "tiny model ran on CUDA with float16")


def manual_items() -> list[Result]:
    return [
        Result(
            "BTC chord model",
            INFO,
            "manual: clone the BTC repo and download its weights (Phase 0)",
            required=False,
        ),
        Result(
            "RMVPE weights",
            INFO,
            "manual: download the RMVPE weights file (Phase 0)",
            required=False,
        ),
        Result(
            "Playwright Chromium",
            INFO,
            "run `python -m playwright install chromium` if not done by setup_windows.bat",
            required=False,
        ),
    ]


def run_checks(deep: bool = False) -> list[Result]:
    prepare_dll_dirs()
    results = [
        check_python(),
        check_cuda(),
        check_binary(
            "ffmpeg", "ffmpeg", "winget install --id Gyan.FFmpeg -e (then a new terminal)"
        ),
        check_binary(
            "Node.js", "node", "winget install --id OpenJS.NodeJS.LTS -e (then a new terminal)"
        ),
        check_binary(
            "rubberband (time-stretch)",
            "rubberband",
            "only needed for slow-down / transpose backing track (Phase 7)",
            required=False,
        ),
    ]

    required_modules = [
        ("FastAPI", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
        ("psutil", "psutil"),
        ("nvidia-ml-py (pynvml)", "pynvml"),
        ("yt-dlp", "yt_dlp"),
        ("soundfile", "soundfile"),
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("librosa", "librosa"),
        ("demucs", "demucs"),
        ("audio-separator", "audio_separator"),
        ("torchcrepe", "torchcrepe"),
        ("faster-whisper", "faster_whisper"),
        ("PyThaiNLP", "pythainlp"),
        ("music21", "music21"),
        ("Playwright", "playwright"),
        ("mir_eval", "mir_eval"),
    ]
    results.extend(check_import(label, module) for label, module in required_modules)

    results.append(
        check_import(
            "beat_this (beat/downbeat)",
            "beat_this",
            hint="pip install https://github.com/CPJKU/beat_this/archive/main.zip",
        )
    )
    results.append(check_ctranslate2_cuda())
    results.append(check_import("pyrubberband", "pyrubberband", required=False))
    if deep:
        results.append(check_whisper_transcribe())
    results.extend(manual_items())
    return results


def exit_code(results: list[Result]) -> int:
    return 1 if any(r.status == FAIL and r.required for r in results) else 0


def format_results(results: list[Result]) -> str:
    lines = []
    for r in results:
        detail = f"  {r.detail}" if r.detail else ""
        lines.append(f"[{r.status}] {r.name}{detail}")
    failed = [r for r in results if r.status == FAIL and r.required]
    lines.append("")
    if failed:
        lines.append(f"{len(failed)} required check(s) failed:")
        lines.extend(f"  - {r.name}" for r in failed)
    else:
        lines.append("All required checks passed.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gracenote Phase 0 environment check")
    parser.add_argument(
        "--deep",
        action="store_true",
        help="also transcribe a short clip with faster-whisper on the GPU (downloads tiny model)",
    )
    args = parser.parse_args(argv)

    results = run_checks(deep=args.deep)
    print(format_results(results))
    return exit_code(results)


if __name__ == "__main__":
    sys.exit(main())
