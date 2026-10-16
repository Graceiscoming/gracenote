# Engineering Standards

มาตรฐานวิศวกรรมของ Gracenote (รายละเอียด) — กฎสั้นที่ Claude Code อ่านทุก session อยู่ใน `CLAUDE.md`

## 1. หลักการ

- **Separation of concerns**: UI, API, domain logic, และ ML models แยกชั้นกันชัดเจน
- **Dependency rule**: ชั้นนอกพึ่งชั้นใน ไม่ใช่ย้อนกลับ
  `frontend → API (FastAPI) → orchestrator → pipeline/ + tab/ (pure domain) → core models`
  โค้ดใน `pipeline/` และ `tab/` ห้าม import FastAPI, React, หรืออะไรที่เกี่ยวกับ HTTP
- **ทุก pipeline stage อยู่หลัง interface เดียวกัน** (ADR 0002) เพื่อสลับ model/library ได้โดยไม่แตะส่วนอื่น
- **KISS / YAGNI**: ทำเท่าที่ Phase ปัจจุบันต้องการ ไม่ abstract ก่อนซ้ำ 3 ครั้ง
- **Fail loudly, recover gracefully**: ไม่กลืน exception แต่แอปต้องไม่ค้าง และบอกผู้ใช้ว่าเกิดอะไรขึ้น
- **Reproducibility**: ผลลัพธ์ของ stage เดียวกัน, input เดียวกัน, params เดียวกัน ต้องได้ผลเหมือนเดิม (ใช้ seed คงที่)

## 2. สถาปัตยกรรมโดยย่อ

ดู `plan.md` หัวข้อ 2 และ 5 สำหรับภาพรวมและ pipeline ส่วนการตัดสินใจเชิงโครงสร้างให้บันทึกเป็น ADR ใน `docs/adr/`

## 3. กลยุทธ์การทดสอบ

| ระดับ | ทดสอบอะไร | รันที่ไหน |
|---|---|---|
| Unit | logic บริสุทธิ์: tab solver, block generator, quantize, key suggestion, cache key, cost function | ทุกที่ (CI + เครื่อง dev) |
| Integration | ต่อ stage กับ stage ด้วยเสียงสังเคราะห์สั้นๆ (sine wave รู้ pitch แน่นอน) | เครื่อง dev (ส่วนใหญ่ mark `gpu`) |
| Benchmark / regression | ความแม่นยำเมโลดี้ด้วย **mir_eval** กับเพลงที่ผู้ใช้แกะมือไว้ (ground truth) | เครื่อง dev |
| Frontend | unit test ของ logic (vitest) + checklist ทดสอบมือสำหรับ piano roll/tab editor | เครื่อง dev |

กติกา:
- **Test-first** เมื่อทำได้ โดยเฉพาะ solver และกฎต่างๆ (เขียนเมโลดี้สั้นๆ + tab ที่คาดหวัง)
- Marker: `gpu` (ต้องใช้ CUDA/โมเดลหนัก), `slow` — CI รัน `pytest -m "not gpu"`
- **ข้อมูลเสียงในเทสต์ต้องสร้างสังเคราะห์** (numpy) หรือเป็นเสียงที่เราอัดเองเท่านั้น ไม่ commit เพลงที่มีลิขสิทธิ์
- แก้ bug = เขียนเทสต์ที่ fail ก่อน แล้วค่อยแก้
- Benchmark เปลี่ยนแล้วต้องบันทึกผลก่อน-หลังใน commit/PR ห้ามแก้ ground truth เพื่อให้ตัวเลขดีขึ้น

## 4. Git workflow

- Trunk-based: `main` ต้องเขียวเสมอ งานทำใน branch สั้นๆ (`feat/piano-roll`, `fix/octave-error`)
- แม้ทำคนเดียวก็เปิด Pull Request (ใช้เป็น self-review และเป็นประวัติใน portfolio)
- **Conventional Commits**: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `perf:`, `chore:`, `ci:`
- คอมมิตเล็ก ทำอย่างเดียวต่อคอมมิต
- ติด tag เมื่อจบแต่ละ Phase (`v0.1.0` = Phase 1 …) และอัปเดต `CHANGELOG.md` (รูปแบบ Keep a Changelog)

## 5. คุณภาพโค้ด

- **ruff** ทำทั้ง lint และ format (config ใน `pyproject.toml`) — ต้องผ่านก่อน commit และใน CI
- Type hints ทุก public function; ข้อมูลข้ามขอบเขต module ใช้ pydantic model
- ฟังก์ชันเล็ก ทำอย่างเดียว ตั้งชื่อให้บอกเจตนา; comment อธิบาย "ทำไม" ไม่ใช่ "ทำอะไร"
- ค่าตัวเลขที่ปรับได้ (threshold, น้ำหนัก cost) อยู่ใน config ไม่ฝังในอัลกอริทึม
- Dependency ใหม่ทุกตัวต้องยืนยันว่าลงบน Windows ได้ และเหตุผลที่เพิ่ม

## 6. Error handling & Logging

- ใช้ exception ชนิดเฉพาะของโปรเจกต์ (เช่น `StageError`, `ModelLoadError`) ไม่ throw `Exception` เปล่าๆ
- Log ต้องมี context: project id, stage, input hash, เวลาที่ใช้
- ข้อความ error ที่ผู้ใช้เห็นเป็นภาษาไทยที่บอกว่าเกิดอะไรและลองทำอะไรต่อ (เช่น "VRAM ไม่พอ ลองลด preset เป็น Fast")
- งานที่รันนานต้องยกเลิกได้ และไม่ทิ้งไฟล์ครึ่งๆ กลางๆ (เขียนลงไฟล์ชั่วคราวแล้ว rename)

## 7. Config & Secrets

- ค่าตั้งผู้ใช้/ค่า default อยู่ในไฟล์ config; ไม่มี secret ในโค้ดหรือ git
- `.env` ถูก ignore; `.claude/settings.local.json` เป็นของส่วนตัว ไม่ commit
- Path ใช้ `pathlib`; ทดสอบกับ path ภาษาไทยและมีช่องว่าง

## 8. เอกสาร

- `README.md`: ภาพรวม วิธีติดตั้ง สถานะ ผลความแม่นยำ
- `docs/adr/`: ทุกการตัดสินใจสำคัญ (ใช้ `/new-adr`)
- `plan.md`: spec และ roadmap — อัปเดตเมื่อสเปกเปลี่ยน
- เอกสารอัปเดตในคอมมิตเดียวกับโค้ดที่เปลี่ยน

## 9. Security & Privacy

- ทำงาน local เป็นหลัก ไม่ส่งเสียงหรือข้อมูลผู้ใช้ออกนอกเครื่อง
- Backend bind ที่ `127.0.0.1` เท่านั้น (ไม่เปิดให้เครื่องอื่นเข้าถึง)
- Validate input จากผู้ใช้ (URL, path, ไฟล์อัปโหลด); ห้ามต่อ string เป็น shell command — ส่ง argument เป็น list
- ล็อกเวอร์ชัน dependency (`requirements.lock.txt`) หลัง Phase 0 ผ่าน

## 10. ลิขสิทธิ์และข้อมูล (สำคัญเมื่อทำเป็น portfolio สาธารณะ)

- การโหลดเพลงจาก YouTube ผิดเงื่อนไขการใช้งานของ YouTube ได้ — เครื่องมือนี้ออกแบบสำหรับ **ฝึกซ้อมส่วนตัว** ใน README ต้องระบุชัดว่าผู้ใช้รับผิดชอบเอง
- **ห้าม commit** ไฟล์เสียง, stems, model weights, ผลที่ได้จากเพลงมีลิขสิทธิ์ (ใช้ `.gitignore`)
- ข้อมูลสำหรับเดโม/benchmark ที่เปิดสาธารณะ: ใช้เสียงที่อัดเอง, เสียงสังเคราะห์, หรือเพลงที่ license อนุญาต (CC0 / CC-BY) และระบุที่มา
- ตัวเลขความแม่นยำที่โชว์ใน README ต้องบอกว่าวัดกับชุดข้อมูลอะไร กี่เพลง

## 11. Definition of Done

งานหนึ่งชิ้นถือว่าเสร็จเมื่อ:
1. โค้ดทำงานตาม spec ของหัวข้อใน plan.md
2. มีเทสต์ และ `pytest -m "not gpu"` ผ่าน
3. `ruff check .` และ `ruff format --check .` ผ่าน
4. เอกสารที่เกี่ยวข้องอัปเดตแล้ว (README / plan.md / ADR / CHANGELOG)
5. ถ้าแตะ pipeline ที่กระทบความแม่นยำ: รัน benchmark แล้วไม่แย่ลง (หรือบันทึกเหตุผลที่ยอมแลก)
6. ได้ทดสอบจริงบนเครื่องเป้าหมายแล้ว หรือระบุชัดว่ายังไม่ได้ทดสอบ

## 12. Portfolio checklist

- [ ] README มี GIF/วิดีโอสั้นของ piano roll + tab editor
- [ ] ตาราง benchmark (เพลงกี่เพลง วัดด้วยอะไร ได้เท่าไร) พร้อมวิธีรันซ้ำ
- [ ] แผนภาพสถาปัตยกรรม + ADR อย่างน้อย 3 ฉบับ
- [ ] CI badge เขียว, เทสต์ครอบคลุม logic หลัก
- [ ] Git history สะอาด (Conventional Commits, PR ต่อฟีเจอร์)
- [ ] Release tag ต่อ Phase + CHANGELOG
- [ ] ระบุ License (ตัดสินใจก่อนเปิด public) และหมายเหตุเรื่องลิขสิทธิ์/การใช้งานส่วนตัว
- [ ] ตรวจชื่อโปรเจกต์ไม่ชนเครื่องหมายการค้าก่อนเปิด public
- [ ] สคริปต์ติดตั้งที่คนอื่นรันตามแล้วใช้งานได้จริง (ทดสอบบนเครื่องสะอาด)
