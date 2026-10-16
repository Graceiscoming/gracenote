import json

import pytest

import make_draft
from label_session import LabelSession
from make_draft import DraftError, check_inputs, write_draft
from notes import Note, read_notes_csv

NOTES = [Note(30.0, 30.5, 60), Note(30.5, 31.0, 62)]


@pytest.fixture
def files(tmp_path):
    audio, code, weights = tmp_path / "a.mp3", tmp_path / "rmvpe.py", tmp_path / "rmvpe.pt"
    for path in (audio, code, weights):
        path.write_bytes(b"x")
    return audio, code, weights


def test_check_inputs_accepts_valid_arguments(files):
    audio, code, weights = files
    check_inputs(audio, 30.0, 60.0, code, weights)


@pytest.mark.parametrize(("start", "end"), [(-1.0, 5.0), (5.0, 5.0), (9.0, 5.0)])
def test_check_inputs_rejects_bad_region(files, start, end):
    audio, code, weights = files
    with pytest.raises(DraftError, match="ช่วงเวลา"):
        check_inputs(audio, start, end, code, weights)


def test_check_inputs_reports_each_missing_file_in_thai(files, tmp_path):
    audio, code, weights = files
    with pytest.raises(DraftError, match="ไฟล์เสียง"):
        check_inputs(tmp_path / "missing.mp3", 0.0, 5.0, code, weights)
    with pytest.raises(DraftError, match="โค้ด RMVPE"):
        check_inputs(audio, 0.0, 5.0, None, weights)
    with pytest.raises(DraftError, match="weights"):
        check_inputs(audio, 0.0, 5.0, code, tmp_path / "missing.pt")


def test_write_draft_outputs_are_readable_by_a_label_session(tmp_path):
    drafts = tmp_path / "drafts"
    audio = tmp_path / "samples" / "song.mp3"
    csv_path = write_draft(drafts, "song", NOTES, audio, 30.0, 60.0)
    assert read_notes_csv(csv_path) == NOTES
    info = json.loads((drafts / "song.draft.json").read_text(encoding="utf-8"))
    assert (info["start_sec"], info["end_sec"]) == (30.0, 60.0)
    session = LabelSession("song", drafts, tmp_path / "gt", root=tmp_path)
    assert session.notes == NOTES
    assert session.range_end == 60.0


def test_main_prints_thai_error_and_returns_1_for_missing_audio(tmp_path, capsys):
    code = make_draft.main(
        [str(tmp_path / "none.mp3"), "--start", "0", "--end", "5", "--drafts-dir", str(tmp_path)]
    )
    assert code == 1
    assert "ไม่พบไฟล์เสียง" in capsys.readouterr().err
