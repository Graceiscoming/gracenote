import json
import wave

import numpy as np
import pytest
from fastapi.testclient import TestClient

from label_session import LabelSession
from label_tool import create_app, pick_song
from notes import Note, read_notes_csv, write_notes_csv

DRAFT = [Note(10.0, 10.5, 60), Note(10.5, 11.0, 62)]


def write_tone_wav(path, seconds=1.0, rate=8000):
    samples = 0.3 * np.sin(2 * np.pi * 440 * np.arange(int(seconds * rate)) / rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes((samples * 32767).astype("<i2").tobytes())


@pytest.fixture
def client(tmp_path):
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    write_notes_csv(drafts / "song.csv", DRAFT)
    info = {"audio": "song.wav", "start_sec": 10.0, "end_sec": 12.0}
    (drafts / "song.draft.json").write_text(json.dumps(info), encoding="utf-8")
    write_tone_wav(tmp_path / "song.wav")
    session = LabelSession("song", drafts, tmp_path / "ground_truth", root=tmp_path)
    return TestClient(create_app(session)), tmp_path


def test_index_page_and_audio_are_served(client):
    web, _ = client
    page = web.get("/")
    assert page.status_code == 200 and "Label Tool" in page.text
    audio = web.get("/audio")
    assert audio.status_code == 200 and audio.content[:4] == b"RIFF"


def test_state_lists_notes_range_and_config(client):
    state = client[0].get("/api/state").json()
    assert [n["pitch"] for n in state["notes"]] == [60, 62]
    assert state["range"] == {"start": 10.0, "end": 12.0}
    assert state["config"]["min_note_sec"] > 0


def test_op_edits_notes_and_returns_new_state(client):
    reply = client[0].post("/api/op", json={"op": "pitch", "args": {"index": 0, "pitch": 65}})
    assert reply.status_code == 200
    assert reply.json()["notes"][0]["pitch"] == 65


def test_rejected_op_returns_400_with_thai_message_and_keeps_notes(client):
    web, _ = client
    reply = web.post(
        "/api/op", json={"op": "add", "args": {"onset": 10.1, "offset": 10.3, "pitch": 70}}
    )
    assert reply.status_code == 400 and "ซ้อน" in reply.json()["detail"]
    assert len(web.get("/api/state").json()["notes"]) == 2


def test_export_without_verified_region_is_400_and_creates_no_file(client):
    web, tmp_path = client
    reply = web.post("/api/export", json={})
    assert reply.status_code == 400 and "verified" in reply.json()["detail"]
    assert not (tmp_path / "ground_truth").exists()


def test_verified_then_export_writes_files_and_second_export_needs_overwrite(client):
    web, tmp_path = client
    assert web.post("/api/verified", json={"start": 10.0, "end": 11.0}).status_code == 200
    reply = web.post("/api/export", json={})
    assert reply.status_code == 200 and reply.json()["note_count"] == 2
    assert read_notes_csv(tmp_path / "ground_truth" / "song.csv") == DRAFT
    assert web.post("/api/export", json={}).status_code == 409
    assert web.post("/api/export", json={"overwrite": True}).status_code == 200


def test_bad_verified_region_is_400(client):
    reply = client[0].post("/api/verified", json={"start": 5.0, "end": 4.0})
    assert reply.status_code == 400


def test_pick_song_uses_only_draft_or_requires_a_name(tmp_path):
    with pytest.raises(SystemExit, match="ไม่มีดราฟต์"):
        pick_song(tmp_path, None)
    (tmp_path / "a.draft.json").write_text("{}", encoding="utf-8")
    assert pick_song(tmp_path, None) == "a"
    (tmp_path / "b.draft.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="--song"):
        pick_song(tmp_path, None)
    assert pick_song(tmp_path, "b") == "b"
    with pytest.raises(SystemExit, match="ไม่พบดราฟต์"):
        pick_song(tmp_path, "zzz")
