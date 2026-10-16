# Gracenote

Local web app (Windows เท่านั้น) ที่แกะเมโลดี้เสียงร้องจากเพลง → piano roll → guitar tab สำหรับมือกีตาร์สายเมโลดี้
โปรเจกต์นี้เป็น **portfolio project** ด้วย: โค้ดต้องอ่านง่าย มีเทสต์ มีเอกสาร และ git history สะอาด

Spec เต็มอยู่ที่ `plan.md` — อ่านเฉพาะหัวข้อของ Phase ที่กำลังทำ ห้ามโหลดทั้งไฟล์โดยไม่จำเป็น
มาตรฐานละเอียด: `docs/ENGINEERING.md` · การตัดสินใจเชิงสถาปัตยกรรม: `docs/adr/` · เป้าหมายแต่ละ Phase: `docs/GOALS.md`

## Commands
- Setup (ครั้งแรก): `setup_windows.bat`
- เช็กการติดตั้ง: `python scripts/check_env.py` (เพิ่ม `--deep` เพื่อถอดเสียงจริงบน GPU ต้องมีอินเทอร์เน็ตโหลดโมเดล tiny)
- Lint / format: `ruff check .` / `ruff format .`
- Test ที่ไม่ใช้ GPU: `pytest -m "not gpu"` · ทั้งหมด: `pytest`
- Run app: `start.bat` (ยังไม่มี — สร้างใน Phase 1)
- Benchmark: `python benchmark/run.py` (ยังไม่มี — สร้างใน Phase 0)

## Domain rules (สำคัญที่สุด)
- Windows เท่านั้น: ห้ามเพิ่ม dependency ที่ลงบน Windows ไม่ได้ (madmom, essentia, vamp) — ก่อนเพิ่ม library ใหม่ต้องยืนยันว่าลงบน Windows ได้
- **pitch ที่ถูกต้องสำคัญกว่าความง่ายในการเล่นเสมอ**: ห้ามเปลี่ยน pitch/octave เองโดยไม่ได้รับการยืนยันจากผู้ใช้
- ทุก pipeline stage อยู่หลัง interface เดียวกัน (input/output ชัด, cache ได้) สลับ model ได้โดยไม่แตะส่วนอื่น (ดู ADR 0002)
- GPU stage รันทีละตัวและคืน VRAM ทุกครั้ง (VRAM 8GB)
- ผล auto กับการแก้ของผู้ใช้เก็บแยกกัน ห้ามเขียนทับ user edits / locked notes
- ตัดโน้ตจากหลายสัญญาณ (energy, onset, voicing) เพราะ F0 อย่างเดียวแยกโน้ต pitch ซ้ำไม่ได้; ขอบคำร้องเป็นแค่ตัวช่วย ไม่ใช่กฎ (ADR 0004)
- ก่อน import faster-whisper/ctranslate2 บน Windows ต้องเรียก `add_nvidia_dll_dirs()` (backend/app/windows_dll.py)
- ค่าตัวเลข (threshold, น้ำหนัก cost) ห้ามฝังในโค้ด ให้อยู่ใน config
- แก้ส่วนที่กระทบความแม่นยำ → รัน benchmark เทียบก่อน-หลัง และบันทึกผล ห้ามแก้ ground truth เพื่อให้ผ่าน
- ห้าม commit ไฟล์เสียง, stems, model weights, หรือไฟล์ใน `projects/` และ `samples/` (ลิขสิทธิ์ + ขนาด)

## Engineering rules
- Python 3.11, type hints ทุก public function, `ruff check` และ `ruff format` ต้องผ่านก่อน commit
- เขียนเทสต์พร้อมโค้ด; logic บริสุทธิ์ (tab solver, block generator, note segmentation, key suggestion) ต้องมี unit test และทำ test-first เมื่อทำได้
- เทสต์ที่ต้องใช้ GPU/โมเดลหนัก mark `@pytest.mark.gpu` (CI ข้ามตัวเหล่านี้) ข้อมูลเสียงในเทสต์ให้สร้างสังเคราะห์ด้วย numpy ไม่ใช้เพลงจริง
- แยกชั้น: API (FastAPI) ไม่มี business logic; logic อยู่ใน `pipeline/` และ `tab/` ซึ่งห้าม import FastAPI
- ฟังก์ชันเล็ก ทำอย่างเดียว; DRY แต่ไม่ abstract ก่อนซ้ำ 3 ครั้ง; ไม่ทำเกินที่ Phase ปัจจุบันต้องการ (YAGNI)
- ห้ามกลืน exception เงียบๆ; log ต้องมี context; ข้อความ error ที่ผู้ใช้เห็นเป็นภาษาไทยที่อ่านรู้เรื่อง
- ใช้ `pathlib`; รองรับ path ภาษาไทย/มีช่องว่างบน Windows; ห้ามฝัง path หรือ secret ส่วนตัว
- การตัดสินใจสำคัญเขียน ADR ใน `docs/adr/` (ใช้ `/new-adr`)
- เอกสารอัปเดตพร้อมโค้ดในคอมมิตเดียวกัน (README / plan.md / CHANGELOG)

## Workflow
- Git: branch ต่อฟีเจอร์ (`feat/…`, `fix/…`), คอมมิตเล็กๆ แบบ Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`), `main` ต้องเขียวเสมอ
- งานใหญ่: อ่านหัวข้อใน plan.md → วางแผนใน plan mode → ทำทีละขั้น → ถามผู้ใช้เมื่อสเปกกำกวม
- Definition of Done: โค้ด + เทสต์ผ่าน + ruff ผ่าน + เอกสารอัปเดต + (ถ้าแตะ pipeline) benchmark ไม่แย่ลง
- ห้ามบอกว่า "เสร็จ" ก่อนรันเช็กจริง — แสดงผลลัพธ์จริงของเทสต์/benchmark
- สิ่งที่ยังไม่ได้ลองบนเครื่องผู้ใช้ (Windows + RTX 4060) ให้บอกชัดว่ายังไม่ได้ทดสอบ อย่าเดา
- ตอบผู้ใช้เป็นภาษาไทย (ศัพท์เทคนิคใช้อังกฤษได้); โค้ด คอมเมนต์ commit และชื่อตัวแปรเป็นอังกฤษ
