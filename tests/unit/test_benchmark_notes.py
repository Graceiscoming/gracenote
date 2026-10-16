import pytest

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

MELODY = [Note(1.0, 1.5, 60), Note(1.5, 2.0, 62), Note(3.0, 3.5, 64)]


def test_csv_round_trip_keeps_notes_and_sorts(tmp_path):
    path = tmp_path / "song.csv"
    write_notes_csv(path, [MELODY[2], MELODY[0], MELODY[1]])
    assert read_notes_csv(path) == MELODY


def test_csv_format_matches_readme_example(tmp_path):
    path = tmp_path / "song.csv"
    write_notes_csv(path, [Note(12.34, 12.81, 64)])
    assert path.read_text(encoding="utf-8") == "onset_sec,offset_sec,midi_pitch\n12.340,12.810,64\n"


def test_read_csv_rejects_wrong_header(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("start,end,pitch\n1,2,60\n", encoding="utf-8")
    with pytest.raises(ValueError, match="header"):
        read_notes_csv(path)


def test_read_csv_rejects_row_with_missing_column(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("onset_sec,offset_sec,midi_pitch\n1.0,2.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="บรรทัด 2"):
        read_notes_csv(path)


def test_add_note_inserts_in_time_order():
    result = add_note(MELODY, 2.2, 2.6, 65)
    assert [n.onset for n in result] == [1.0, 1.5, 2.2, 3.0]


def test_add_note_rejects_overlap_and_leaves_input_unchanged():
    original = list(MELODY)
    with pytest.raises(NoteEditError, match="ซ้อน"):
        add_note(MELODY, 1.4, 1.8, 65)
    assert original == MELODY


def test_add_note_rejects_too_short_and_bad_pitch():
    with pytest.raises(NoteEditError, match="สั้น"):
        add_note(MELODY, 5.0, 5.001, 60)
    with pytest.raises(NoteEditError, match="pitch"):
        add_note(MELODY, 5.0, 5.5, 128)


def test_delete_note_removes_only_that_note():
    assert delete_note(MELODY, 1) == [MELODY[0], MELODY[2]]


def test_edit_with_bad_index_is_rejected():
    for func in (lambda: delete_note(MELODY, 3), lambda: set_pitch(MELODY, -1, 60)):
        with pytest.raises(NoteEditError, match="ไม่พบโน้ต"):
            func()


def test_move_note_shifts_onset_and_offset():
    result = move_note(MELODY, 2, -0.5)
    assert result[2] == Note(2.5, 3.0, 64)


def test_move_note_into_neighbour_is_rejected():
    with pytest.raises(NoteEditError, match="ซ้อน"):
        move_note(MELODY, 2, -1.2)


def test_resize_note_changes_edges_only():
    assert resize_note(MELODY, 0, 0.8, 1.5)[0] == Note(0.8, 1.5, 60)


def test_resize_note_to_touch_neighbour_is_allowed():
    assert resize_note(MELODY, 1, 1.5, 3.0)[1] == Note(1.5, 3.0, 62)


def test_set_pitch_changes_only_pitch():
    assert set_pitch(MELODY, 1, 74)[1] == Note(1.5, 2.0, 74)


def test_split_note_makes_two_halves_with_same_pitch():
    result = split_note(MELODY, 0, 1.2)
    assert result[:2] == [Note(1.0, 1.2, 60), Note(1.2, 1.5, 60)]
    assert len(result) == 4


def test_split_note_outside_or_too_close_to_edge_is_rejected():
    for at in (0.9, 1.51, 1.001, 1.499):
        with pytest.raises(NoteEditError, match="จุดตัด"):
            split_note(MELODY, 0, at)


def test_merge_notes_spans_both_and_longer_note_decides_pitch():
    notes = [Note(1.0, 1.2, 60), Note(1.2, 2.0, 62)]
    assert merge_notes(notes, 0) == [Note(1.0, 2.0, 62)]


def test_merge_notes_tie_keeps_first_pitch():
    assert merge_notes(MELODY, 0)[0] == Note(1.0, 2.0, 60)


def test_merge_last_note_is_rejected():
    with pytest.raises(NoteEditError, match="ถัดไป"):
        merge_notes(MELODY, 2)


def test_split_then_merge_restores_note():
    assert merge_notes(split_note(MELODY, 0, 1.2), 0) == MELODY


def test_notes_in_region_separates_inside_and_crossing():
    inside, crossing = notes_in_region(MELODY, 1.2, 3.2)
    assert inside == [MELODY[1]]
    assert crossing == [MELODY[0], MELODY[2]]


def test_notes_in_region_includes_notes_touching_the_boundaries():
    inside, crossing = notes_in_region(MELODY, 1.0, 3.5)
    assert inside == MELODY
    assert crossing == []


def test_notes_in_region_ignores_notes_outside():
    inside, crossing = notes_in_region(MELODY, 2.2, 2.9)
    assert inside == [] and crossing == []
