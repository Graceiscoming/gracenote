"""Local web page for correcting a machine draft into benchmark ground truth.

    python benchmark/label_tool.py            # opens the only draft in benchmark/drafts/
    python benchmark/label_tool.py --song sample1 --open

The page plays the original audio, shows the draft on a piano roll, and lets you edit notes
and mark a verified region. This module is only the thin web layer; all rules live in
``label_session.py`` and ``notes.py``. Export (the only write into ground_truth/) happens
when you press the export button.
"""

from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from label_session import ExportError, ExportExistsError, LabelSession
from notes import NoteEditError

BENCHMARK_DIR = Path(__file__).resolve().parent
ROOT = BENCHMARK_DIR.parent
UI_FILE = BENCHMARK_DIR / "label_ui" / "index.html"
DEFAULT_DRAFTS_DIR = BENCHMARK_DIR / "drafts"
DEFAULT_GROUND_TRUTH_DIR = BENCHMARK_DIR / "ground_truth"
DEFAULT_PORT = 8765


class OpBody(BaseModel):
    op: str
    args: dict[str, Any] = {}


class VerifiedBody(BaseModel):
    start: float | None = None
    end: float | None = None


class ExportBody(BaseModel):
    overwrite: bool = False


def _error(status: int, message: str) -> JSONResponse:
    return JSONResponse({"detail": message}, status_code=status)


def create_app(session: LabelSession) -> FastAPI:
    app = FastAPI(title="Gracenote label tool")

    @app.get("/")
    def page() -> FileResponse:
        return FileResponse(UI_FILE)

    @app.get("/audio")
    def audio() -> FileResponse:
        return FileResponse(session.audio_path)

    @app.get("/api/state")
    def state() -> dict[str, Any]:
        return session.state()

    @app.post("/api/op")
    def op(body: OpBody):
        try:
            session.apply(body.op, body.args)
        except NoteEditError as error:
            return _error(400, str(error))
        return session.state()

    @app.post("/api/verified")
    def verified(body: VerifiedBody):
        try:
            session.set_verified(body.start, body.end)
        except ExportError as error:
            return _error(400, str(error))
        return session.state()

    @app.post("/api/export")
    def export(body: ExportBody):
        try:
            result = session.export(overwrite=body.overwrite)
        except ExportExistsError as error:
            return _error(409, str(error))
        except ExportError as error:
            return _error(400, str(error))
        return {
            "csv": str(result.csv_path),
            "meta": str(result.meta_path),
            "note_count": result.note_count,
            "crossing_count": result.crossing_count,
        }

    return app


def pick_song(drafts_dir: Path, song: str | None) -> str:
    drafts = sorted(p.name.removesuffix(".draft.json") for p in drafts_dir.glob("*.draft.json"))
    if song:
        if song not in drafts:
            raise SystemExit(f"ไม่พบดราฟต์ '{song}' ใน {drafts_dir} (ต้องรัน make_draft.py ก่อน)")
        return song
    if len(drafts) == 1:
        return drafts[0]
    if not drafts:
        raise SystemExit(f"ไม่มีดราฟต์ใน {drafts_dir} — รัน benchmark/make_draft.py ก่อน")
    raise SystemExit(f"มีหลายดราฟต์ ({', '.join(drafts)}) — ระบุด้วย --song")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--song", help="draft name (default: the only draft in the folder)")
    parser.add_argument("--drafts-dir", type=Path, default=DEFAULT_DRAFTS_DIR)
    parser.add_argument("--ground-truth-dir", type=Path, default=DEFAULT_GROUND_TRUTH_DIR)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--open", action="store_true", help="open the page in the browser")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # Thai text must not crash a cp1252 console
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parse_args(argv)
    song = pick_song(args.drafts_dir, args.song)
    session = LabelSession(song, args.drafts_dir, args.ground_truth_dir, root=ROOT)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"เปิด {url}  (เพลง: {song}, กด Ctrl+C เพื่อหยุด)")
    if args.open:
        webbrowser.open(url)
    uvicorn.run(create_app(session), host="127.0.0.1", port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
