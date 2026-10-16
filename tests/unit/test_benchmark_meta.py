import json

import pytest

from meta import GroundTruthMeta, read_meta, write_meta


def test_meta_round_trip_and_default_provenance(tmp_path):
    path = tmp_path / "song.meta.json"
    write_meta(path, GroundTruthMeta("song", 10.0, 40.5, 12))
    assert read_meta(path) == GroundTruthMeta("song", 10.0, 40.5, 12)
    assert json.loads(path.read_text(encoding="utf-8"))["provenance"] == (
        "machine draft, human verified"
    )


def test_meta_file_has_expected_keys(tmp_path):
    path = tmp_path / "song.meta.json"
    write_meta(path, GroundTruthMeta("song", 1.0, 2.0, 3))
    assert set(json.loads(path.read_text(encoding="utf-8"))) == {
        "song",
        "verified_start_sec",
        "verified_end_sec",
        "note_count",
        "provenance",
    }


def test_meta_rejects_empty_or_reversed_region():
    for start, end in ((5.0, 5.0), (6.0, 5.0)):
        with pytest.raises(ValueError, match="verified_end_sec"):
            GroundTruthMeta("song", start, end, 0)
