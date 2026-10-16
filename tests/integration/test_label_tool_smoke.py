"""Browser smoke test for the labeling page: load it, mark a verified region, export a CSV."""

import json
import socket
import threading
import time
import wave

import numpy as np
import pytest
import uvicorn

from label_session import LabelSession
from label_tool import create_app
from notes import Note, read_notes_csv, write_notes_csv

pytestmark = pytest.mark.slow

DRAFT = [Note(10.0, 10.5, 60), Note(10.5, 11.0, 62), Note(12.0, 12.5, 64)]


def write_tone_wav(path, seconds=14.0, rate=8000):
    samples = 0.3 * np.sin(2 * np.pi * 440 * np.arange(int(seconds * rate)) / rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes((samples * 32767).astype("<i2").tobytes())


@pytest.fixture
def server(tmp_path):
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    write_notes_csv(drafts / "song.csv", DRAFT)
    info = {"audio": "song.wav", "start_sec": 10.0, "end_sec": 13.0}
    (drafts / "song.draft.json").write_text(json.dumps(info), encoding="utf-8")
    write_tone_wav(tmp_path / "song.wav")
    session = LabelSession("song", drafts, tmp_path / "ground_truth", root=tmp_path)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    config = uvicorn.Config(create_app(session), host="127.0.0.1", port=port, log_level="error")
    srv = uvicorn.Server(config)
    thread = threading.Thread(target=srv.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not srv.started and time.time() < deadline:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}/", tmp_path / "ground_truth"
    srv.should_exit = True
    thread.join(timeout=5)


def test_page_loads_marks_verified_region_and_exports_csv(server):
    sync_api = pytest.importorskip("playwright.sync_api")
    url, ground_truth = server
    with sync_api.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as error:  # Chromium not installed: python -m playwright install chromium
            pytest.skip(f"Chromium is not available: {error}")
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(url)
        page.wait_for_function("window.gracenote.state.notes.length === 3")
        assert "song" in page.inner_text("#song")

        page.fill("#v-start", "10")
        page.press("#v-start", "Tab")
        page.fill("#v-end", "11.2")
        page.press("#v-end", "Tab")
        page.wait_for_function("window.gracenote.state.verified !== null")

        page.click("#btn-export")
        page.wait_for_function("document.getElementById('status').textContent.startsWith('ส่งออก')")
        assert "ส่งออก 2 โน้ต" in page.inner_text("#status")
        browser.close()

    assert errors == []
    assert read_notes_csv(ground_truth / "song.csv") == DRAFT[:2]
    meta = json.loads((ground_truth / "song.meta.json").read_text(encoding="utf-8"))
    assert meta["provenance"] == "machine draft, human verified"
    assert (meta["verified_start_sec"], meta["verified_end_sec"]) == (10.0, 11.2)
