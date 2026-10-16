import json

import pytest

from label_session import ExportError, ExportExistsError, LabelSession
from meta import read_meta
from notes import Note, NoteEditError, read_notes_csv, write_notes_csv

DRAFT = [Note(10.0, 10.5, 60), Note(10.5, 11.0, 62), Note(12.0, 12.5, 64), Note(20.0, 20.5, 65)]


@pytest.fixture
def folders(tmp_path):
    drafts, truth = tmp_path / "drafts", tmp_path / "ground_truth"
    drafts.mkdir()
    write_notes_csv(drafts / "song.csv", DRAFT)
    info = {"audio": "samples/song.mp3", "start_sec": 10.0, "end_sec": 30.0}
    (drafts / "song.draft.json").write_text(json.dumps(info), encoding="utf-8")
    return drafts, truth


def make_session(folders, tmp_path):
    drafts, truth = folders
    return LabelSession("song", drafts, truth, root=tmp_path)


def test_new_session_loads_draft_notes_and_range(folders, tmp_path):
    state = make_session(folders, tmp_path).state()
    assert [n["pitch"] for n in state["notes"]] == [60, 62, 64, 65]
    assert state["verified"] is None
    assert state["range"] == {"start": 10.0, "end": 30.0}


def test_audio_path_is_resolved_against_root(folders, tmp_path):
    session = make_session(folders, tmp_path)
    assert session.audio_path == (tmp_path / "samples" / "song.mp3").resolve()


def test_edit_is_applied_and_saved_so_a_new_session_sees_it(folders, tmp_path):
    session = make_session(folders, tmp_path)
    session.apply("pitch", {"index": 0, "pitch": 72})
    session.set_verified(10.0, 15.0)
    reopened = make_session(folders, tmp_path)
    assert reopened.notes[0].pitch == 72
    assert reopened.verified == (10.0, 15.0)


def test_each_operation_is_dispatched(folders, tmp_path):
    session = make_session(folders, tmp_path)
    session.apply("add", {"onset": 13.0, "offset": 13.5, "pitch": 67})
    session.apply("move", {"index": 3, "delta": 0.1})
    session.apply("resize", {"index": 3, "onset": 13.1, "offset": 13.4})
    session.apply("split", {"index": 3, "at": 13.25})
    session.apply("merge", {"index": 3})
    session.apply("delete", {"index": 3})
    assert session.notes == sorted(DRAFT, key=lambda n: n.onset)


def test_rejected_edit_leaves_notes_and_saved_file_unchanged(folders, tmp_path):
    session = make_session(folders, tmp_path)
    with pytest.raises(NoteEditError, match="ซ้อน"):
        session.apply("add", {"onset": 10.2, "offset": 10.4, "pitch": 70})
    assert session.notes == DRAFT
    assert not (folders[0] / "song.work.json").exists()


def test_unknown_operation_and_missing_arguments_are_rejected(folders, tmp_path):
    session = make_session(folders, tmp_path)
    with pytest.raises(NoteEditError, match="ไม่รู้จัก"):
        session.apply("explode", {})
    with pytest.raises(NoteEditError, match="ไม่ครบ"):
        session.apply("move", {"index": 0})


def test_verified_region_can_be_cleared_and_must_be_ordered(folders, tmp_path):
    session = make_session(folders, tmp_path)
    session.set_verified(10.0, 15.0)
    session.set_verified(None, None)
    assert session.verified is None
    with pytest.raises(ExportError, match="มากกว่า"):
        session.set_verified(15.0, 15.0)


def test_export_without_verified_region_is_refused_and_writes_nothing(folders, tmp_path):
    session = make_session(folders, tmp_path)
    with pytest.raises(ExportError, match="verified"):
        session.export()
    assert not folders[1].exists()


def test_export_writes_only_notes_inside_verified_region_with_meta(folders, tmp_path):
    session = make_session(folders, tmp_path)
    session.set_verified(10.0, 12.25)  # cuts through the note at 12.0-12.5
    result = session.export()
    assert read_notes_csv(result.csv_path) == DRAFT[:2]
    assert (result.note_count, result.crossing_count) == (2, 1)
    meta = read_meta(result.meta_path)
    assert (meta.verified_start_sec, meta.verified_end_sec) == (10.0, 12.25)
    assert meta.provenance == "machine draft, human verified"
    assert meta.song == "song" and meta.note_count == 2


def test_export_uses_edited_notes_not_the_original_draft(folders, tmp_path):
    session = make_session(folders, tmp_path)
    session.apply("pitch", {"index": 0, "pitch": 61})
    session.set_verified(10.0, 11.0)
    assert read_notes_csv(session.export().csv_path)[0].pitch == 61


def test_export_refuses_to_overwrite_without_confirmation(folders, tmp_path):
    session = make_session(folders, tmp_path)
    session.set_verified(10.0, 11.0)
    first = session.export()
    session.apply("pitch", {"index": 0, "pitch": 70})
    with pytest.raises(ExportExistsError, match="เขียนทับ"):
        session.export()
    assert read_notes_csv(first.csv_path)[0].pitch == 60
    session.export(overwrite=True)
    assert read_notes_csv(first.csv_path)[0].pitch == 70


def test_export_never_touches_the_drafts_folder(folders, tmp_path):
    session = make_session(folders, tmp_path)
    session.set_verified(10.0, 11.0)
    before = {p.name for p in folders[0].iterdir()}
    session.export()
    assert {p.name for p in folders[0].iterdir()} - before == set()
