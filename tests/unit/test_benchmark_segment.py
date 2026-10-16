import numpy as np

from label_config import SegmentationConfig
from notes import Note
from segment import f0_to_notes, hz_to_midi

CONFIG = SegmentationConfig()
HOP = CONFIG.hop_sec


def midi_to_hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def track(*parts: tuple[float, float]) -> np.ndarray:
    """Build an F0 track from (midi or 0 for silence, seconds) parts."""
    frames = []
    for midi, seconds in parts:
        hz = 0.0 if midi == 0 else midi_to_hz(midi)
        frames.extend([hz] * round(seconds / HOP))
    return np.array(frames)


def test_hz_to_midi_maps_a4_and_marks_unvoiced_as_nan():
    midi = hz_to_midi(np.array([440.0, 0.0, 220.0]))
    assert midi[0] == 69 and midi[2] == 57 and np.isnan(midi[1])


def test_two_pitches_become_two_notes_with_times():
    notes = f0_to_notes(track((60, 0.5), (62, 0.5)))
    assert notes == [Note(0.0, 0.5, 60), Note(0.5, 1.0, 62)]


def test_offset_shifts_all_times():
    notes = f0_to_notes(track((60, 0.4)), offset_sec=12.0)
    assert notes == [Note(12.0, 12.4, 60)]


def test_silence_between_notes_splits_them_and_leading_silence_is_skipped():
    notes = f0_to_notes(track((0, 0.3), (60, 0.4), (0, 0.3), (60, 0.4)))
    assert notes == [Note(0.3, 0.7, 60), Note(1.0, 1.4, 60)]


def test_short_unvoiced_gap_does_not_split_a_note():
    notes = f0_to_notes(track((60, 0.3), (0, 0.04), (60, 0.3)))
    assert len(notes) == 1 and notes[0].pitch == 60


def test_short_pitch_blip_is_absorbed_into_the_neighbour():
    notes = f0_to_notes(track((60, 0.4), (64, 0.03), (60, 0.4)))
    assert len(notes) == 1 and notes[0].pitch == 60
    assert notes[0].offset - notes[0].onset > 0.8


def test_note_shorter_than_minimum_is_dropped():
    assert f0_to_notes(track((60, 0.04))) == []


def test_small_vibrato_around_one_pitch_stays_one_note():
    t = np.arange(0, 0.8, HOP)
    midi = 60 + 0.3 * np.sin(2 * np.pi * 5.5 * t)
    notes = f0_to_notes(440.0 * 2 ** ((midi - 69) / 12))
    assert [n.pitch for n in notes] == [60]


def test_empty_or_all_unvoiced_track_gives_no_notes():
    assert f0_to_notes(np.array([])) == []
    assert f0_to_notes(np.zeros(100)) == []
