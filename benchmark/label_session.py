"""State of one labeling session: draft notes, edits, verified region and export.

No web code lives here (the FastAPI layer in ``label_tool.py`` only forwards calls), so every
rule can be unit-tested. Edits are saved after each change to ``<song>.work.json`` in the
drafts folder, so closing the browser never loses work. The only code that writes into the
ground-truth folder is :meth:`LabelSession.export`, which runs when the user asks for it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from label_config import EDIT, EditConfig
from meta import GroundTruthMeta, write_meta
from notes import (
    Note,
    NoteEditError,
    add_note,
    delete_note,
    merge_notes,
    move_note,
    notes_in_region,
    read_notes_csv,
    resize_note,
    set_pitch,
    split_note,
    write_notes_csv,
)


class ExportError(ValueError):
    """Export is not possible yet; ``str(error)`` is a Thai message for the user."""


class ExportExistsError(ExportError):
    """The ground-truth file already exists and overwrite was not confirmed."""


@dataclass(frozen=True)
class ExportResult:
    csv_path: Path
    meta_path: Path
    note_count: int
    crossing_count: int  # notes left out because they cross a verified-region boundary


class LabelSession:
    def __init__(
        self,
        song: str,
        drafts_dir: Path,
        ground_truth_dir: Path,
        root: Path,
        config: EditConfig = EDIT,
    ) -> None:
        self.song = song
        self.ground_truth_dir = ground_truth_dir
        self.config = config
        self._work_path = drafts_dir / f"{song}.work.json"
        info = json.loads((drafts_dir / f"{song}.draft.json").read_text(encoding="utf-8"))
        self.audio_path = (root / info["audio"]).resolve()
        self.range_start = float(info["start_sec"])
        self.range_end = float(info["end_sec"])
        self.verified: tuple[float, float] | None = None
        self.notes: list[Note] = read_notes_csv(drafts_dir / f"{song}.csv")
        self._load_work()

    def _load_work(self) -> None:
        if not self._work_path.exists():
            return
        data = json.loads(self._work_path.read_text(encoding="utf-8"))
        self.notes = [Note(n["onset"], n["offset"], n["pitch"]) for n in data["notes"]]
        if data["verified"]:
            self.verified = (data["verified"]["start"], data["verified"]["end"])

    def _save_work(self) -> None:
        data = {"notes": self._notes_json(), "verified": self._verified_json()}
        temp = self._work_path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        temp.replace(self._work_path)

    def _notes_json(self) -> list[dict[str, Any]]:
        return [{"onset": n.onset, "offset": n.offset, "pitch": n.pitch} for n in self.notes]

    def _verified_json(self) -> dict[str, float] | None:
        if self.verified is None:
            return None
        return {"start": self.verified[0], "end": self.verified[1]}

    def state(self) -> dict[str, Any]:
        return {
            "song": self.song,
            "notes": self._notes_json(),
            "verified": self._verified_json(),
            "range": {"start": self.range_start, "end": self.range_end},
            "config": {
                "default_new_note_sec": self.config.default_new_note_sec,
                "min_note_sec": self.config.min_note_sec,
            },
        }

    def apply(self, op: str, args: dict[str, Any]) -> None:
        """Run one edit by name; raises NoteEditError (Thai message) if it is rejected."""
        cfg, notes = self.config, self.notes
        try:
            if op == "add":
                new = add_note(notes, args["onset"], args["offset"], args["pitch"], cfg)
            elif op == "delete":
                new = delete_note(notes, args["index"])
            elif op == "move":
                new = move_note(notes, args["index"], args["delta"], cfg)
            elif op == "resize":
                new = resize_note(notes, args["index"], args["onset"], args["offset"], cfg)
            elif op == "pitch":
                new = set_pitch(notes, args["index"], args["pitch"], cfg)
            elif op == "split":
                new = split_note(notes, args["index"], args["at"], cfg)
            elif op == "merge":
                new = merge_notes(notes, args["index"])
            else:
                raise NoteEditError(f"ไม่รู้จักคำสั่ง '{op}'")
        except (KeyError, TypeError) as error:
            raise NoteEditError("ข้อมูลคำสั่งแก้โน้ตไม่ครบหรือไม่ถูกต้อง") from error
        self.notes = new
        self._save_work()

    def set_verified(self, start: float | None, end: float | None) -> None:
        """Mark [start, end] as verified, or clear it when both are None."""
        if start is None or end is None:
            self.verified = None
        elif end <= start:
            raise ExportError("ช่วงที่ตรวจแล้วต้องมีจุดสิ้นสุดมากกว่าจุดเริ่มต้น")
        else:
            self.verified = (start, end)
        self._save_work()

    def export(self, overwrite: bool = False) -> ExportResult:
        """Write ``<song>.csv`` and ``<song>.meta.json`` with only the verified notes."""
        if self.verified is None:
            raise ExportError("ยังไม่ได้เลือกช่วงที่ตรวจแล้ว (verified) จึงยังส่งออกไม่ได้")
        csv_path = self.ground_truth_dir / f"{self.song}.csv"
        meta_path = self.ground_truth_dir / f"{self.song}.meta.json"
        if (csv_path.exists() or meta_path.exists()) and not overwrite:
            raise ExportExistsError(f"มีไฟล์ {csv_path.name} อยู่แล้ว ต้องยืนยันก่อนเขียนทับ")
        start, end = self.verified
        inside, crossing = notes_in_region(self.notes, start, end)
        self.ground_truth_dir.mkdir(parents=True, exist_ok=True)
        write_notes_csv(csv_path, inside, self.config)
        write_meta(meta_path, GroundTruthMeta(self.song, start, end, len(inside)))
        return ExportResult(csv_path, meta_path, len(inside), len(crossing))
