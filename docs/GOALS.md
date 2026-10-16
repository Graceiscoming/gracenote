# /goal ข้อความสำเร็จรูปแต่ละ Phase

`/goal` คือคำสั่งใน Claude Code ที่ตั้ง "เงื่อนไขสำเร็จ" แล้วให้ Claude ทำต่อเองจนเงื่อนไขนั้นผ่าน ตัวตัดสินดูจากสิ่งที่ปรากฏในบทสนทนาเท่านั้น (ไม่ได้รันคำสั่งเอง) ดังนั้นทุกข้อให้ Claude **รันเช็กแล้วแสดงผลจริง**

วิธีใช้: เปิด session ใหม่ต่อ 1 Phase → เข้า plan mode ให้วางแผนก่อน → วางข้อความ `/goal` ของ Phase นั้น
ทุกข้อมีเงื่อนไขหยุดตาม turn กันวนไม่รู้จบ ปรับได้ตามต้องการ

> ค่าที่เป็น `<...>` เติมหลังรู้ผลจริง (เช่น baseline จาก Phase 0) ก่อนใช้ goal ของ Phase ถัดไป
> ผู้ใช้ต้องเตรียมเอง: เพลงทดสอบ 3–5 นาทีใน `samples/` และ ground truth ใน `benchmark/ground_truth/` (ดู `benchmark/README.md`)

---

## Phase 0 — Setup & Benchmark

**0a. สภาพแวดล้อม**
```
/goal python scripts/check_env.py --deep exits 0 with every required check PASS (show the full output), pytest -m "not gpu" passes, ruff check . passes, and docs/PHASE0_REPORT.md lists measured wall time and peak VRAM for the separation, F0 and whisper stages on the song in samples/. Do not edit scripts/check_env.py to make a check pass. Stop after 30 turns.
```

**0b. Benchmark**
```
/goal python benchmark/run.py exists, runs on every song in benchmark/ground_truth/, and prints note-level precision, recall and F1 (mir_eval, 50 ms onset tolerance) per song and on average; the result table is saved to docs/BENCHMARK.md; unit tests cover the metric code. Do not modify any ground truth file. Stop after 25 turns.
```

## Phase 1 — Audio → Piano Roll (MVP)
```
/goal a local audio file in samples/ goes through ingest, separation, F0 and note segmentation and produces melody.json; the piano roll page shows notes labelled with name and octave (save a Playwright screenshot to docs/img/pianoroll.png); pytest -m "not gpu" and ruff pass; benchmark average note F1 is recorded in docs/BENCHMARK.md and is at least <BASELINE_F1>. Stop after 40 turns.
```

## Phase 2 — Analysis (key, tempo, chords, lyrics, structure)
```
/goal key, BPM, time signature, beat grid, chords, lyrics with word timestamps and section boundaries are produced for the benchmark songs and stored in the project; chord sheet view and beat-synced metronome work in the browser; each analysis stage has a unit or integration test; docs/BENCHMARK.md reports chord and beat accuracy against ground truth where available. Stop after 40 turns.
```

## Phase 3 — Guitar Tab + Block Mode + Playability
```
/goal the tab solver turns melody.json into a tab, Block Mode (strict and soft) keeps every note inside the selected blocks, a feasibility report shows block coverage, and the pitch of no note is ever changed (assert this in a test); unit tests cover at least 15 hand-written melody cases; pytest and ruff pass. Stop after 40 turns.
```

## Phase 4 — Tab Editor
```
/goal in the browser any single note in the tab can be selected by clicking it and edited (fret, string, timing, technique, delete) without touching other notes; locked notes survive a re-solve; undo and redo cover every edit; frontend logic tests pass. Show test output. Stop after 40 turns.
```

## Phase 5 — Vocal techniques + Key suggestion
```
/goal slide, hammer-on, pull-off, bend and vibrato suggestions are generated from F0 contours with accept/reject in the UI and per-technique on/off settings; key/capo/tuning suggestions rank at least the top 5 options with reasons; unit tests cover each technique rule with synthetic pitch contours; pytest and ruff pass. Stop after 35 turns.
```

## Phase 6 — Export + Project/Cache + Status
```
/goal each section can be exported as PNG, SVG and PDF; reopening a saved project does not re-run any cached stage (prove it with log output); the status bar shows stage, percent, ETA and GPU/VRAM/CPU/RAM during a run; a cancelled run leaves no partial files. Stop after 40 turns.
```

## Phase 7 — Polish
```
/goal loop A-B with slow-down, backing track mode and fretboard diagram work; README has a demo GIF, benchmark table, architecture diagram and install steps; CHANGELOG and v1.0.0 tag notes are written; CI is green. Stop after 40 turns.
```
