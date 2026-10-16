"""Note model, CSV read/write and pure editing operations for the labeling tool.

All editing functions take a sorted list of notes and return a new sorted list; they never
mutate their input. The melody is monophonic, so edits that would make notes overlap are
rejected with :class:`NoteEditError` (the message is Thai because the user sees it).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, replace
from pathlib import Path

from label_config import EDIT, EditConfig

CSV_HEADER = ["onset_sec", "offset_sec", "midi_pitch"]


class NoteEditError(ValueError):
    """An edit was rejected; ``str(error)`` is a Thai message for the user."""


@dataclass(frozen=True)
class Note:
    onset: float
    offset: float
    pitch: int

    @property
    def duration(self) -> float:
        return self.offset - self.onset


def sort_notes(notes: list[Note]) -> list[Note]:
    return sorted(notes, key=lambda n: (n.onset, n.offset))


def _check_note(note: Note, config: EditConfig) -> None:
    if note.offset - note.onset < config.min_note_sec - config.overlap_tolerance_sec:
        raise NoteEditError(f"โน้ตสั้นเกินไป (ต้องยาวอย่างน้อย {config.min_note_sec} วินาที)")
    if not config.midi_min <= note.pitch <= config.midi_max:
        raise NoteEditError(f"pitch ต้องอยู่ระหว่าง {config.midi_min}-{config.midi_max}")
    if note.onset < 0:
        raise NoteEditError("เวลาเริ่มต้องไม่ติดลบ")


def _check_index(notes: list[Note], index: int) -> None:
    if not 0 <= index < len(notes):
        raise NoteEditError("ไม่พบโน้ตที่เลือก")


def _validated(notes: list[Note], config: EditConfig) -> list[Note]:
    result = sort_notes(notes)
    for left, right in zip(result, result[1:], strict=False):
        if left.offset > right.onset + config.overlap_tolerance_sec:
            raise NoteEditError("โน้ตซ้อนทับกัน (เมโลดี้ต้องไม่ซ้อน) ลองย่อโน้ตข้างเคียงก่อน")
    return result


def _replace_at(notes: list[Note], index: int, new: Note, config: EditConfig) -> list[Note]:
    _check_index(notes, index)
    _check_note(new, config)
    return _validated([new if i == index else n for i, n in enumerate(notes)], config)


def add_note(
    notes: list[Note], onset: float, offset: float, pitch: int, config: EditConfig = EDIT
) -> list[Note]:
    new = Note(onset, offset, pitch)
    _check_note(new, config)
    return _validated([*notes, new], config)


def delete_note(notes: list[Note], index: int) -> list[Note]:
    _check_index(notes, index)
    return [n for i, n in enumerate(notes) if i != index]


def move_note(
    notes: list[Note], index: int, delta_sec: float, config: EditConfig = EDIT
) -> list[Note]:
    _check_index(notes, index)
    note = notes[index]
    moved = replace(note, onset=note.onset + delta_sec, offset=note.offset + delta_sec)
    return _replace_at(notes, index, moved, config)


def resize_note(
    notes: list[Note], index: int, onset: float, offset: float, config: EditConfig = EDIT
) -> list[Note]:
    _check_index(notes, index)
    return _replace_at(notes, index, replace(notes[index], onset=onset, offset=offset), config)


def set_pitch(notes: list[Note], index: int, pitch: int, config: EditConfig = EDIT) -> list[Note]:
    _check_index(notes, index)
    return _replace_at(notes, index, replace(notes[index], pitch=pitch), config)


def split_note(notes: list[Note], index: int, at: float, config: EditConfig = EDIT) -> list[Note]:
    """Split one note into two at time ``at``; both halves keep the pitch."""
    _check_index(notes, index)
    note = notes[index]
    slack = config.overlap_tolerance_sec
    if (
        not note.onset + config.min_note_sec - slack
        <= at
        <= note.offset - config.min_note_sec + slack
    ):
        raise NoteEditError("จุดตัดต้องอยู่ภายในโน้ต และเหลือความยาวแต่ละท่อนพอ")
    first = Note(note.onset, at, note.pitch)
    second = Note(at, note.offset, note.pitch)
    return [*notes[:index], first, second, *notes[index + 1 :]]


def merge_notes(notes: list[Note], index: int) -> list[Note]:
    """Merge note ``index`` with the next one; the longer note decides the pitch."""
    _check_index(notes, index)
    if index + 1 >= len(notes):
        raise NoteEditError("ไม่มีโน้ตถัดไปให้รวม")
    first, second = notes[index], notes[index + 1]
    pitch = first.pitch if first.duration >= second.duration else second.pitch
    merged = Note(first.onset, second.offset, pitch)
    return [*notes[:index], merged, *notes[index + 2 :]]


def notes_in_region(notes: list[Note], start: float, end: float) -> tuple[list[Note], list[Note]]:
    """Return (notes fully inside [start, end], notes that cross a region boundary)."""
    inside = [n for n in notes if n.onset >= start and n.offset <= end]
    crossing = [n for n in notes if n.offset > start and n.onset < end and n not in inside]
    return inside, crossing


def write_notes_csv(path: Path, notes: list[Note], config: EditConfig = EDIT) -> None:
    decimals = config.csv_decimals
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(CSV_HEADER)
        for n in sort_notes(notes):
            writer.writerow([f"{n.onset:.{decimals}f}", f"{n.offset:.{decimals}f}", n.pitch])


def read_notes_csv(path: Path) -> list[Note]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header != CSV_HEADER:
            raise ValueError(f"{path.name}: header ต้องเป็น {','.join(CSV_HEADER)} แต่พบ {header}")
        notes = []
        for line_no, row in enumerate(reader, start=2):
            if len(row) != 3:
                raise ValueError(f"{path.name} บรรทัด {line_no}: ต้องมี 3 คอลัมน์")
            notes.append(Note(float(row[0]), float(row[1]), int(row[2])))
    return sort_notes(notes)
