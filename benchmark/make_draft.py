"""Make a machine draft of the melody for one part of a song, to be corrected by hand.

    python benchmark/make_draft.py samples/sample1.mp3 --start 30 --end 75 --rmvpe-code <rmvpe.py>

Steps: cut the region with ffmpeg -> separate vocals (Demucs, GPU, own process so VRAM is
freed) -> RMVPE F0 -> pitch-change segmentation -> ``benchmark/drafts/<song>.csv`` plus
``<song>.draft.json`` (audio path and region). Note times are on the original song's timeline.
The drafts folder is git-ignored. Open the result with ``python benchmark/label_tool.py``.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from label_config import SEGMENTATION
from notes import Note, write_notes_csv
from segment import f0_to_notes

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DRAFTS_DIR = Path(__file__).resolve().parent / "drafts"
DEFAULT_WEIGHTS = ROOT / "models" / "rmvpe.pt"
RMVPE_CODE_ENV = "GRACENOTE_RMVPE_CODE"


class DraftError(RuntimeError):
    """A draft step failed; ``str(error)`` is a Thai message for the user."""


def check_inputs(audio: Path, start: float, end: float, code: Path | None, weights: Path) -> None:
    if not audio.is_file():
        raise DraftError(f"ไม่พบไฟล์เสียง: {audio}")
    if start < 0 or end <= start:
        raise DraftError("ช่วงเวลาไม่ถูกต้อง: ต้อง 0 <= --start < --end")
    if code is None or not code.is_file():
        raise DraftError(
            f"ไม่พบโค้ด RMVPE: ระบุ --rmvpe-code (หรือตั้ง {RMVPE_CODE_ENV}) "
            "ชี้ไปที่ infer/rmvpe.py ของโปรเจกต์ RVC"
        )
    if not weights.is_file():
        raise DraftError(f"ไม่พบ weights ของ RMVPE: {weights}")


def run_command(cmd: list[str], what: str) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        tail = (result.stderr or result.stdout)[-600:]
        raise DraftError(f"{what} ล้มเหลว (exit {result.returncode}): {tail}")


def cut_region(audio: Path, start: float, end: float, out_wav: Path) -> None:
    run_command(
        ["ffmpeg", "-y", "-v", "error", "-ss", str(start), "-to", str(end), "-i", str(audio),
         "-ar", "44100", "-ac", "2", str(out_wav)],
        "ตัดช่วงเสียงด้วย ffmpeg",
    )  # fmt: skip


def separate_vocals(clip_wav: Path, work_dir: Path) -> Path:
    run_command(
        [sys.executable, "-m", "demucs", "--two-stems=vocals", "-d", "cuda", "-o", str(work_dir),
         str(clip_wav)],
        "แยกเสียงร้องด้วย Demucs",
    )  # fmt: skip
    return work_dir / "htdemucs" / clip_wav.stem / "vocals.wav"


def write_draft(
    drafts_dir: Path, song: str, notes: list[Note], audio: Path, start: float, end: float
) -> Path:
    """Write ``<song>.csv`` and ``<song>.draft.json``; return the CSV path."""
    drafts_dir.mkdir(parents=True, exist_ok=True)
    csv_path = drafts_dir / f"{song}.csv"
    write_notes_csv(csv_path, notes)
    try:
        audio_ref = audio.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        audio_ref = str(audio.resolve())
    info = {"audio": audio_ref, "start_sec": start, "end_sec": end}
    (drafts_dir / f"{song}.draft.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    return csv_path


def make_draft(args: argparse.Namespace) -> Path:
    code = args.rmvpe_code or (
        Path(os.environ[RMVPE_CODE_ENV]) if RMVPE_CODE_ENV in os.environ else None
    )
    check_inputs(args.audio, args.start, args.end, code, args.rmvpe_weights)
    from rmvpe_rvc import extract_f0  # imported late: pulls in torch

    with tempfile.TemporaryDirectory(prefix="gracenote_draft_") as tmp:
        work = Path(tmp)
        clip = work / "clip.wav"
        cut_region(args.audio, args.start, args.end, clip)
        vocals = separate_vocals(clip, work)
        f0 = extract_f0(vocals, code, args.rmvpe_weights, SEGMENTATION.rmvpe_threshold)
    notes = f0_to_notes(f0, offset_sec=args.start)
    song = args.name or args.audio.stem
    csv_path = write_draft(args.drafts_dir, song, notes, args.audio, args.start, args.end)
    print(f"สร้างดราฟต์ {len(notes)} โน้ต -> {csv_path}")
    return csv_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("audio", type=Path, help="original song, e.g. samples/sample1.mp3")
    parser.add_argument("--start", type=float, required=True, help="region start (seconds)")
    parser.add_argument("--end", type=float, required=True, help="region end (seconds)")
    parser.add_argument("--name", help="song name for the output files (default: audio file name)")
    parser.add_argument(
        "--rmvpe-code", type=Path, help=f"RVC infer/rmvpe.py (or env {RMVPE_CODE_ENV})"
    )
    parser.add_argument("--rmvpe-weights", type=Path, default=DEFAULT_WEIGHTS)
    parser.add_argument("--drafts-dir", type=Path, default=DEFAULT_DRAFTS_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # Thai text must not crash a cp1252 console
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        make_draft(parse_args(argv))
    except DraftError as error:
        print(f"ผิดพลาด: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
