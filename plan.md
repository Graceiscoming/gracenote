# 🎸 Gracenote — แผนพัฒนาโปรแกรมแกะเมโลดี้เสียงร้อง → Piano Roll → Guitar Tab

> เครื่องมือสำหรับมือกีตาร์สายเมโลดี้: ใส่ลิงก์ YouTube หรือไฟล์เสียง → ได้เมโลดี้เสียงร้องเป็นโน้ตแม่นๆ + key / BPM / time signature / คอร์ด / เนื้อเพลง → สร้าง Tab กีตาร์ที่เล่นง่ายและอยู่ใน block ที่เลือก → แก้ไขได้ทุกตัว → export เป็นรูปทีละท่อน

---

## 0. สรุปเป้าหมาย

| เรื่อง | รายละเอียด |
|---|---|
| ผู้ใช้ | มือกีตาร์สายเมโลดี้ (ใช้คนเดียว รันบนเครื่องตัวเอง) |
| ปัญหาที่แก้ | ขั้นตอน "ฟัง → แกะ → ลองเล่น → เขียน tab → export" ใช้เวลานานและต้องทำมือทั้งหมด |
| สิ่งที่สำคัญที่สุด | **ความแม่นยำของโน้ตเมโลดี้** (pitch + จังหวะ) รองลงมาคือความเร็วและใช้งานง่าย |
| แนวทาง | Local-first: ประมวลผลบนเครื่องเองด้วย GPU, ไม่ต้องพึ่ง cloud |
| ภาษา UI | ไทย/อังกฤษ (สลับชื่อโน้ต C D E ↔ โด เร มี ได้) |

### Workflow เดิม vs ใหม่

| ขั้นตอนเดิม (มือ) | ขั้นตอนใหม่ (โปรแกรม) |
|---|---|
| 1. โหลดเพลงจาก YouTube | วางลิงก์ → ระบบโหลดให้ (yt-dlp) |
| 2. ฟังและแกะเมโลดี้ | แยกเสียงร้อง → ตรวจ pitch → ตัดโน้ต → snap เข้า key → แสดงบน piano roll |
| 3. เล่นเป็น line กีตาร์ | กดสร้าง Tab อัตโนมัติ (เลือก block ได้) + ฟังเสียงตัวอย่าง |
| 4. เขียนโน้ตเป็น tab | แก้ tab ได้โดยคลิกที่ตัวโน้ตตัวนั้นเลย |
| 5. Export ทีละท่อนเป็นรูป | เลือกท่อน → export PNG/SVG/PDF |

---

## 1. ฟีเจอร์ทั้งหมด (จัดกลุ่ม)

### A. Ingestion
- วางลิงก์ YouTube หรืออัปโหลดไฟล์เสียง (mp3, wav, flac, m4a, ogg)
- ดาวน์โหลดด้วย **yt-dlp** + แปลงเป็น WAV 44.1kHz ด้วย **ffmpeg**
- ดึง metadata (ชื่อเพลง ศิลปิน ความยาว thumbnail) เก็บใน project
- รองรับ playlist ทีละหลายเพลง (คิวงาน) — Phase ท้ายๆ

### B. Audio Analysis (หลังบ้านหลัก)
1. **Source separation** — แยก vocals / instrumental (และแยก lead vocal ออกจากประสาน)
2. **Key detection** — ตรวจ key + scale (major/minor, modes) และตรวจ **modulation** (เปลี่ยน key กลางเพลง)
3. **Tempo / Beat / Downbeat / Time signature** — สร้าง beat grid และ tempo map (รองรับเพลงที่ tempo แกว่ง)
4. **Chord detection** — ตรวจคอร์ดตามจังหวะ (maj, min, 7, maj7, m7, sus, dim, aug, slash chord)
5. **Lyrics** — ถอดเนื้อร้อง + จัดตำแหน่งคำตามเวลา (รองรับไทย/อังกฤษ) หรือให้ผู้ใช้วางเนื้อเองแล้ว align
6. **Song structure** — แบ่งท่อน (Intro / Verse / Pre-chorus / Chorus / Bridge / Outro) เพื่อใช้ export ทีละท่อน

### C. Melody Transcription (หัวใจ)
- F0 tracking จากเสียงร้อง → segment เป็นโน้ต
- Key-aware snapping + tuning offset correction
- แสดงบน **Piano Roll** พร้อมชื่อโน้ตและ octave (เช่น `E4`, `F#3`) บนทุกตัว
- ค่า **confidence** ต่อโน้ต (ตัวไหนไม่มั่นใจจะเน้นสี)

### D. Chord Sheet View (แบบเว็บแจกคอร์ด)
- เนื้อเพลงอยู่ข้างล่าง คอร์ดอยู่ข้างบนตรงคำที่เปลี่ยนคอร์ดจริง
- คลิกคำ/คอร์ดแล้วเพลงเล่นจากตรงนั้น, auto-scroll ตามเพลง, ไฮไลต์บรรทัดปัจจุบัน
- ปรับ transpose คอร์ดได้, แสดงไดอะแกรมคอร์ด

### E. Metronome / Click Track
- ติ๊กเปิดแล้วมีเสียงเคาะตรงจังหวะเพลงจริง (ตาม beat grid ที่ตรวจได้ ไม่ใช่ BPM คงที่)
- เน้น downbeat (จังหวะ 1) เสียงต่างจากจังหวะอื่น
- ปรับ offset ละเอียด (ms), count-in ก่อนเริ่ม, เลือกความถี่ (1/4, 1/8), ปรับ volume

### F. Auto Guitar Tab
- แปลงเมโลดี้ → (string, fret) ด้วย algorithm หาตำแหน่งที่เล่นง่ายที่สุด
- **Block Mode** — ผู้ใช้เลือก block (ช่วงเฟร็ต/ท่าสเกล) ของ key นั้น แล้วโน้ตทั้งหมดจะอยู่ใน block ที่เลือก แต่กระจายไปทุกสายได้
- **Playability Engine** — ถ้าโน้ตอยู่ไกลกันเกินไป ให้หาวิธีเล่นที่ง่ายที่สุดแต่ยังเป็นโน้ตที่ถูกต้อง

### G. Vocal → Guitar Techniques
- แปลงลูกเล่นเสียงร้อง (สไลด์เสียง, ฟอลล์, วิบราโต, เสียงเอื้อน) เป็นเทคนิคกีตาร์เป็น suggestion ให้ accept/reject

### H. Tab Editor
- คลิกที่โน้ตตัวไหนก็แก้ตัวนั้นได้ทันที (ไม่ต้องลบย้อนจากท้าย)
- เปลี่ยนสาย/เฟร็ต, ลบ, เพิ่ม, เลื่อนจังหวะ, ปรับความยาว, ใส่ slide / hammer-on / pull-off / bend / vibrato ฯลฯ
- Undo/Redo ไม่จำกัด

### I. Smart Key Suggestion
- แนะนำ key ที่เล่นง่ายกว่า key ต้นฉบับ (พร้อม capo / tuning ถ้าเหมาะ) พร้อมคะแนนและเหตุผล

### J. Export
- Export ทีละท่อนเป็น PNG / SVG / PDF (เลือกจำนวน bar ต่อบรรทัด, ใส่คอร์ด/เนื้อ/มาตรฐานโน้ต)
- Export อื่นๆ: MIDI, MusicXML, Guitar Pro (.gp), alphaTex

### K. Project & Cache
- บันทึกโปรเจกต์ (autosave), เปิดต่อได้, cache ทุกขั้นตอนเพื่อไม่ต้องประมวลผลซ้ำ

### L. Status & System Monitor
- แถบสถานะบอกว่าระบบกำลังทำอะไร, % ความคืบหน้า, ETA, GPU / VRAM / CPU / RAM, log, ปุ่มยกเลิก

---

## 2. สถาปัตยกรรมระบบ

```
┌──────────────────────────── Frontend (React + TypeScript + Vite) ────────────────────────────┐
│  Piano Roll (Canvas/WebGL) │ Chord Sheet │ Tab Editor (alphaTab + custom layer) │ Status Bar │
│  Web Audio API: player, stems mixer, metronome, synth preview                                  │
└──────────────▲───────────────────────────────▲────────────────────────────────────────────────┘
               │ REST (HTTP)                   │ WebSocket (progress + system stats, ทุก 500ms)
┌──────────────┴───────────────────────────────┴────────────────────────────────────────────────┐
│                               Backend (Python 3.11 + FastAPI)                                  │
│  API layer ─ Job Manager ─ Pipeline Orchestrator ─ Cache Manager ─ Project Store (SQLite)      │
└───────┬───────────────────────────┬──────────────────────────────┬───────────────────────────┘
        │ GPU Worker (1 process)    │ CPU Worker Pool (N procs)    │ Exporter (headless render)
        │ Demucs/RoFormer, RMVPE/   │ beat/key/chord/structure,    │ SVG→PNG/PDF
        │ CREPE, Whisper            │ tab solver, quantize         │
        └───────────────────────────┴──────────────────────────────┴───────────────────────────┘
                              Storage: projects/<id>/ (audio, stems, json, cache, exports)
```

### หลักการออกแบบ
- **Windows ล้วน + Local web app** — หลังบ้าน Python (FastAPI) รันบนเครื่อง Windows ของผู้ใช้โดยตรง (ไม่ใช้ Ubuntu/WSL2) แล้วเปิดหน้าโปรแกรมผ่านเบราว์เซอร์ที่ `localhost` ไม่ใช่เว็บบนเซิร์ฟเวอร์
- เปิดใช้งานด้วยไฟล์ `start.bat` อันเดียว (เปิด backend + เด้งเบราว์เซอร์ให้เอง)
- ค่อยห่อเป็นแอปเดสก์ท็อป `.exe` ด้วย **Tauri** ทีหลังถ้าต้องการ (Phase 7) โดยไม่ต้องเขียนใหม่
- **ทุก stage อยู่หลัง interface เดียวกัน** เพื่อสลับ model/library ได้ง่ายถ้า library ไหนลงบน Windows ไม่ได้
- **ไม่ต้องใช้ Redis/Celery** — ใช้ job queue ในโปรเซสเดียวกับ `multiprocessing` พอ (เครื่องเดียว ผู้ใช้เดียว) ลดความซับซ้อน
- **Pipeline แบ่งเป็น stage อิสระ** แต่ละ stage มี input/output ชัดเจน, cache ได้, รันซ้ำเฉพาะ stage ที่เปลี่ยนได้
- **Data model กลางเป็น JSON ของเราเอง** (ไม่ผูกกับ format ใด) แล้วค่อย convert ไป alphaTex / MusicXML / GP / MIDI ตอน export

---

## 3. Tech Stack

### Backend
| ส่วน | เทคโนโลยี | หมายเหตุ |
|---|---|---|
| Web framework | **FastAPI** + Uvicorn | REST + WebSocket |
| ดาวน์โหลด | **yt-dlp**, **ffmpeg** | |
| แยกเสียง | **Demucs (htdemucs / htdemucs_ft)** และ/หรือ **BS-RoFormer / MDX-Net** ผ่าน `python-audio-separator` | เลือก model ตามคุณภาพ/ความเร็ว; มี model แยก lead vs backing vocal (karaoke models) |
| F0 / Pitch | **RMVPE** (หลัก, ดีกับเสียงร้อง) + **CREPE (full)** (ตัวช่วยโหวต) + **pYIN** (fallback บน CPU) | ใช้ ensemble ตามค่า confidence |
| Key | chroma (CQT, **librosa**) ของ instrumental stem + Krumhansl–Schmuckler หลายโปรไฟล์ (Krumhansl / Temperley / Edma) โหวตรวมกัน เขียนเองทั้งหมด | ไม่ใช้ essentia เพราะไม่มี wheel ทางการบน Windows |
| Beat/Downbeat | **beat_this** (PyTorch ล้วน ติดตั้งง่ายบน Windows) + librosa เป็น fallback | ไม่ใช้ madmom เพราะ build บน Windows ยาก |
| Chord | **BTC** (PyTorch) เป็นตัวหลัก + beat-synchronous smoothing; **chroma + template + HMM/Viterbi** เขียนเองเป็น fallback; เทียบแหล่งเสียง instrumental stem vs mix ใน benchmark | ไม่ใช้ Chordino/vamp และ Autochord (ใช้ TensorFlow + Vamp plugin, รองรับแค่ major/minor); โค้ด BTC เป็นงานวิจัย อาจต้องปรับให้เข้ากับ PyTorch เวอร์ชันปัจจุบัน → ต้องทดสอบใน Phase 0 |
| Music theory | **music21** | ชั้นทฤษฎีดนตรี: สะกดชื่อโน้ต/คอร์ดตาม key, สเกล/โหมด, interval, transpose, เช็ก key จากโน้ตจริง, MusicXML; ไม่ใช่ตัวฟังเสียง (ดูหัวข้อ 8B) |
| Lyrics | **faster-whisper (large-v3)** บน vocal stem + **WhisperX**/wav2vec2 forced alignment + **PyThaiNLP** ตัดคำไทย | ตรวจภาษาอัตโนมัติ, รับเนื้อที่ผู้ใช้วางเองได้ |
| Structure | self-similarity matrix (chroma + MFCC, **librosa**) + beat-synchronous segmentation | ใช้เป็นค่าเริ่มต้น ผู้ใช้ลาก marker แก้เองได้ (allin1 พึ่ง madmom/natten จึงไม่ใช้) |
| เวลา/ความเร็วเล่น | **rubberband** / SoundTouch | ชะลอโดยไม่เปลี่ยน pitch, transpose backing |
| Tab solver | Python + NumPy/Numba (Viterbi / DP) | |
| Monitor | `psutil`, `nvidia-ml-py (pynvml)` | CPU/RAM/GPU/VRAM |
| Storage | **SQLite** (metadata, undo history) + ไฟล์ใน folder | |
| Export render | **Playwright (headless Chromium)** หรือ resvg/cairosvg | SVG → PNG/PDF คุณภาพสูง |
| ประเมินผล | **mir_eval** | วัดความแม่นยำกับชุดทดสอบ |

### Frontend
| ส่วน | เทคโนโลยี |
|---|---|
| Framework | **React + TypeScript + Vite**, state ด้วย **Zustand** |
| Piano roll | **Canvas 2D / PixiJS (WebGL)** — เรนเดอร์โน้ตเป็นพันตัวได้ลื่น |
| Tab render / playback | **alphaTab** (render tab + โน้ตมาตรฐาน, เล่นเสียง, export SVG) + layer แก้ไขของเราเอง |
| Audio | **Web Audio API** (AudioWorklet สำหรับ metronome แม่นๆ), multi-stem mixer |
| UI | Tailwind CSS + dark theme, shortcut keyboard ครบ |

---

## 4. สเปกเครื่อง & แผนดึงประสิทธิภาพ

**เครื่อง:** Intel i5-13500HX (6P + 8E core, 20 threads) · RTX 4060 Laptop 8GB VRAM · RAM 32GB

### กลยุทธ์
1. **GPU เป็นลำดับ (sequential)** — งานที่ใช้ GPU (แยกเสียง → F0 → Whisper) รันทีละ model เพื่อไม่ให้ VRAM เกิน 8GB; ทุกครั้งที่จบ stage ให้ `del model; torch.cuda.empty_cache()`
2. **ใช้ fp16 / autocast** กับทุก model ที่รองรับ (RTX 40-series มี Tensor Core) เพื่อลดเวลาและ VRAM
3. **ประมวลผลแบบ chunk** — Demucs/RoFormer ใช้ segment + overlap (ปรับ segment size ตาม VRAM ที่เหลือ), เปิด `--shifts` เฉพาะโหมดคุณภาพสูง
4. **รัน CPU stage คู่ขนานกับ GPU stage** — ระหว่างที่ GPU แยกเสียง ให้ CPU ทำ beat/key/chord จาก mix ต้นฉบับไปก่อน (chord/key ที่ละเอียดกว่าค่อยรันซ้ำบน instrumental stem ทีหลัง)
5. **CPU pool** — ใช้ 12–16 worker process (P-core เป็นหลัก) สำหรับงานเบา, จำกัด `torch.set_num_threads` ไม่ให้แย่งกัน
6. **RAM 32GB** — mmap ไฟล์เสียง, เก็บ stem ล่าสุดไว้ใน RAM cache (LRU), ไม่อ่านดิสก์ซ้ำ
7. **ONNX Runtime / TensorRT (ทางเลือก)** — แปลง RMVPE/CREPE เป็น ONNX เพื่อเร่ง inference เพิ่ม (ทำหลังมี baseline แล้วเท่านั้น)
8. **Preset คุณภาพ**
   - ⚡ *Fast*: htdemucs, RMVPE อย่างเดียว, Whisper medium
   - ⚖️ *Balanced* (ค่าเริ่มต้น): htdemucs_ft/RoFormer, RMVPE+CREPE, Whisper large-v3
   - 🎯 *Max accuracy*: แยก 2 รอบ (vocals → lead), ensemble หลาย model, TTA
9. **Benchmark ตั้งแต่ Phase 0** — วัดเวลา/VRAM จริงของแต่ละ stage บนเครื่องนี้ แล้วปรับ preset ตามข้อมูลจริง (อย่าเดา)

> เวลาประมวลผลคาดการณ์คร่าวๆ สำหรับเพลง ~4 นาที ใน preset Balanced น่าจะอยู่ราว 1.5–3 นาทีต่อเพลง — **เป็นเพียงประมาณการ ต้องวัดจริงใน Phase 0**

### การติดตั้งบน Windows (Windows native)

- **Python 3.10 หรือ 3.11** ใน venv แยกของโปรเจกต์
- **PyTorch + CUDA**: ลงจาก index ทางการของ PyTorch ให้ตรงกับเวอร์ชันไดรเวอร์ NVIDIA ที่ติดตั้งอยู่ (เช็กด้วย `nvidia-smi`)
- **ffmpeg**: `winget install ffmpeg` แล้วตรวจว่าอยู่ใน PATH
- **faster-whisper**: ต้องมี CUDA/cuDNN DLLs ครบ — CTranslate2 รุ่น 4.5.0 ขึ้นไปใช้ **cuDNN 9** (error ที่เจอคือ `cudnn_ops64_9.dll`; `cudnn_ops_infer64_8.dll` เป็นของ cuDNN 8 รุ่นเก่า) วิธีแก้: ลง `nvidia-cublas-cu12` และ `nvidia-cudnn-cu12` (9.x) ผ่าน pip (อยู่ใน requirements.txt แล้ว) แล้วเรียก `app.windows_dll.add_nvidia_dll_dirs()` **ก่อน** import faster-whisper/ctranslate2 (ฟังก์ชันนี้เพิ่มโฟลเดอร์ `site-packages\nvidia\*\bin` เข้า DLL search path และ PATH ของโปรเซส) PyTorch 2.4 ขึ้นไปมาพร้อม cuDNN 9 อยู่แล้ว การ import torch ก่อนอาจช่วยบน Windows ตรวจจริงด้วย `check_env.py --deep`
- **Node.js (LTS)** สำหรับ frontend
- ใช้ **beat_this + librosa** แทน madmom/essentia/Chordino/allin1 เพราะติดตั้งบน Windows ยาก
- เปิดใช้งานผ่าน `start.bat`
- **WSL2 เป็นทางหนีทีไล่เท่านั้น**: ถ้าเจอ library ที่จำเป็นจริงๆ แต่ลงบน Windows ไม่ได้ ค่อยย้ายเฉพาะ stage นั้นไปรันใน WSL2 (GPU ใช้ผ่าน WSL2 ได้เต็ม และเรียกผ่าน localhost ได้เหมือนเดิม) ไม่จำเป็นต้องย้ายทั้งโปรเจกต์
- ต้องยืนยันบนเครื่องจริงใน Phase 0 ก่อน ยังไม่ได้ลองติดตั้งจริง

---

## 5. Pipeline การประมวลผล (Workflow หลังบ้าน)

```
[Input: YouTube URL / ไฟล์เสียง]
        │
 S1 ──► Ingest: yt-dlp → WAV 44.1k stereo + loudness normalize (เก็บต้นฉบับไว้)
        │
 S2 ──► Source Separation (GPU): vocals.wav / instrumental.wav → (lead.wav / backing.wav)
        │
        ├─► S3 [CPU, ขนานกัน] Beat/Downbeat/Tempo map/Time signature
        │
 S4 ──► Key Detection (บน instrumental + vocal chroma) → key, scale, ช่วง modulation, tuning offset (cents)
        │
 S5 ──► F0 Tracking (GPU): RMVPE + CREPE → โหวต → แก้ octave error → voicing mask
        │
 S6 ──► Note Segmentation: F0 → โน้ต (onset/offset/pitch/confidence) + ตรวจลูกเล่นเสียง (slide/vibrato/bend)
        │
 S7 ──► Key-aware Snap + Quantize (display grid) → Melody JSON
        │
 S8 ──► Chord Detection (บน instrumental, sync กับ beat)
        │
 S9 ──► Lyrics: Whisper → word timestamps → จัดเข้ากับคอร์ด/บรรทัด
        │
 S10 ─► Structure Segmentation (ท่อน)
        │
 S11 ─► Easy-key Suggestion
        │
[พร้อมแสดงผล]  →  ผู้ใช้เลือก Block → S12 Tab Generation → แก้ไข → Export
```

### รายละเอียดขั้นตอนสำคัญ

**S4 — Key detection (ส่งผลต่อความแม่นยำโดยตรง)**
- คำนวณ chroma (CQT) จาก instrumental stem (ไม่โดนเสียงร้องที่มี vibrato/เอื้อนรบกวน) + จาก vocal stem แล้วถ่วงน้ำหนัก
- เทียบ profile (Krumhansl / Temperley / Edma) หลายแบบ แล้วโหวต
- ใช้ sliding window ตรวจ modulation; ถ้ามี → แบ่งช่วง key ให้แต่ละท่อน
- ประมาณ **tuning offset** (เพลงที่จูนเพี้ยนจาก A=440 เช่น −30 cents) แล้วชดเชยก่อนแปลง Hz → โน้ต
- ผลลัพธ์: key + ความมั่นใจ + alternative (relative major/minor) ให้ผู้ใช้ยืนยัน/เปลี่ยนเองได้ (เปลี่ยนแล้ว S7 รันใหม่เฉพาะส่วนที่ได้ผล)

**S5 — F0 tracking**
- รัน RMVPE และ CREPE บน lead vocal stem; รวมผลด้วย confidence-weighted voting
- แก้ octave jump ด้วย Viterbi/median ตามความต่อเนื่อง
- ตัดช่วงไม่มีเสียงร้อง (voicing) ด้วย threshold ปรับได้

**S6 — Note segmentation**
- ใช้ hysteresis + ความเสถียรของ pitch + onset detection จาก energy/spectral flux
- เก็บ **pitch contour ดิบ** ของแต่ละโน้ตไว้ด้วย (ใช้ตรวจ slide/bend/vibrato ใน Section 8)
- กรองโน้ตสั้นผิดปกติ/โน้ตรบกวน (ลมหายใจ, ตัว s/sh)
- **ปัญหา pitch ซ้ำ:** F0 contour บอกแค่ความถี่ ไม่บอกจุดตัดโน้ต ถ้านักร้องร้องโน้ตเดิมซ้ำ (เช่น "ลา-ลา-ลา" ที่ C4 เท่ากัน) เส้น F0 จะเป็นเส้นเรียบเส้นเดียว ถ้าใช้ความเสถียรของ pitch อย่างเดียวจะได้ 1 โน้ตยาวแทน 3 โน้ต
- **วิธีแก้: รวมสัญญาณหลายอย่างเพื่อ "สับ" โน้ตที่ pitch เดียวกัน** (ADR 0004)
  1. จุดที่ energy (RMS) ของ vocal stem ตกลงระหว่างพยางค์
  2. onset strength (spectral flux) จาก librosa
  3. ช่วงที่เสียงขาด (voicing gap)
  4. ขอบคำจาก lyrics alignment (S9) เป็น **ตัวช่วย (soft hint) เท่านั้น ไม่ใช่กฎตายตัว** เพราะจำนวนโน้ตไม่เท่ากับจำนวนคำ: เสียงเอื้อนมีหลายโน้ตในพยางค์เดียว และบางพยางค์ลากข้ามหลายโน้ต; faster-whisper ให้ timestamp ระดับคำ ไม่ใช่ phoneme และความละเอียดกับเสียงร้องต้องวัดจริง
  5. (ตัวเลือก) Basic Pitch ช่วยตรวจ onset — ต้องผ่านเช็กลิสต์ Phase 0 ว่าลงบน Windows ได้และไม่ตีกับ PyTorch ก่อนใช้
- ผู้ใช้ **แยก/รวมโน้ตเองใน piano roll** ได้เสมอ (split/merge) เป็นตาข่ายสุดท้าย
- เทสต์แบบ test-first ด้วยเสียงสังเคราะห์: sine pitch เดียวกัน 3 ครั้งพร้อมช่วง energy ตก ต้องได้ 3 โน้ต และ benchmark ต้องรายงาน onset F1 แยกให้เห็นกรณี pitch ซ้ำ

**S7 — Key-aware snapping (ไม่ใช่การบังคับ)**
- ถ้า pitch เฉลี่ยของโน้ตอยู่ใกล้ scale degree (±35 cents) → snap เข้าโน้ตใน key
- ถ้าโน้ตเสถียร อยู่นอก key จริง (chromatic / borrowed note) → **คงไว้** และติดป้ายว่า out-of-key
- ถ้าไม่แน่ใจ → ไม่ snap แต่ติด flag confidence ต่ำให้ผู้ใช้ตรวจ
- Quantize เป็นเพียง "display grid" (1/8, 1/16, triplet) โดยเก็บเวลาจริงไว้ด้วยเสมอ เพื่อไม่เสีย feel ของนักร้อง

---

## 6. Piano Roll (ตามที่ขอ: โน้ตวิ่งๆ + บอกชื่อโน้ต)

- แนวนอนเป็นเวลา (sync กับ beat grid), แนวตั้งเป็น pitch, คีย์เปียโนอยู่ด้านซ้ายพร้อมชื่อ `C4`, `D#4` ฯลฯ
- **ทุกโน้ตแสดงป้ายชื่อ + octave** (สลับ C-D-E / โด-เร-มี / scale degree 1-7 ได้)
- **Playhead** วิ่งตามเพลง, โน้ตที่กำลังเล่นไฮไลต์, ซูมเวลา/pitch ได้
- Lane ซ้อนหลายชั้น: waveform · beat grid + เลขห้อง · คอร์ด · เนื้อเพลง · โครงสร้างท่อน
- สีโน้ต: ตาม confidence (เขียว = มั่นใจ, เหลือง = ตรวจซ้ำ, แดง = ไม่มั่นใจ) หรือตาม scale degree / out-of-key
- ซ้อนเส้น **F0 contour ดิบ** ไว้บนโน้ตเพื่อเทียบว่าตัดโน้ตตรงไหม
- คลิกโน้ต = audition เสียงทันที; ลาก/ปรับ/ลบ/เพิ่มโน้ตได้ (เป็นขั้นตรวจแก้ก่อนสร้าง tab)
- ตัวเลือกเสียง: เล่นเสียงร้องต้นฉบับ / เล่นเมโลดี้สังเคราะห์ / เล่นทั้งสองพร้อมกันเพื่อ A/B เทียบความตรง / mute-solo แต่ละ stem

> หมายเหตุ octave: Piano roll แสดง **concert pitch** (เสียงจริง, C4 = middle C = MIDI 60). ส่วนโน้ตมาตรฐานของกีตาร์เขียนสูงกว่าเสียงจริง 1 octave → ระบบ handle ให้อัตโนมัติและมีป้ายกำกับชัดเจนในทั้งสองมุมมอง

---

## 7. Chord Sheet + Metronome

### Chord Sheet
- แปลง chord timeline + word timestamps → บรรทัดเนื้อเพลง โดยวางชื่อคอร์ดตรงเหนือคำที่ตรงกับจังหวะที่คอร์ดเปลี่ยน
- แบ่งตามท่อน (Verse/Chorus…) ตามข้อ S10
- ไฮไลต์ตำแหน่งปัจจุบันตามเพลง, auto-scroll, คลิกเพื่อกระโดดไปเล่น
- แก้คอร์ด/เนื้อ/ตำแหน่งได้, transpose, ซ่อน/แสดงไดอะแกรมคอร์ด, พิมพ์ได้

### Metronome
- ใช้ **beat grid จริงของเพลง** (ไม่ใช่ BPM คงที่) → เคาะตรงแม้ tempo แกว่ง
- เล่นด้วย **AudioWorklet** + lookahead scheduling เพื่อลด jitter, sync กับ AudioContext time ของเพลง
- ตัวเลือก: เน้น downbeat, subdivision, count-in, offset (±ms), เปิดเมื่อ loop section
- โหมดฝึก: ปรับความเร็ว 50–120% โดยไม่เปลี่ยน pitch (rubberband), loop A–B

---

## 8. Auto Guitar Tab (หัวใจที่สอง)

### 8.1 Data model ของโน้ตในแทป
```jsonc
{
  "id": "n_0123",
  "pitch": 64,              // MIDI (เสียงจริง)
  "string": 2, "fret": 5,   // 1 = สายเล็กสุด
  "startBeat": 12.5, "durBeat": 0.5,
  "techniques": ["slide_up"],  // hammer, pull, bend(+1), vibrato, slide_in, slide_out ...
  "confidence": 0.91,
  "source": "auto" | "user"    // แยก auto กับที่ผู้ใช้แก้ เพื่อไม่ทับตอนรันใหม่
}
```

### 8.2 Fingering solver (หาตำแหน่งที่เล่นง่ายที่สุด)
- แต่ละโน้ตมี **candidate (string, fret)** ได้หลายตำแหน่ง (เช่น E4 = สาย 1 เฟร็ต 0, สาย 2 เฟร็ต 5, สาย 3 เฟร็ต 9 ...)
- ใช้ **Viterbi / Dynamic Programming** เลือกลำดับตำแหน่งที่ cost รวมต่ำสุด
- Cost function (ปรับน้ำหนักได้ใน Settings):
  | ปัจจัย | คำอธิบาย |
  |---|---|
  | Hand shift | ระยะเลื่อนมือระหว่างโน้ตติดกัน (เฟร็ต) — ยิ่งมากยิ่งแพง, **ถ่วงตามความเร็ว** (โน้ตเร็ว + เลื่อนไกล = แพงมาก) |
  | Stretch | ช่วงนิ้วที่ต้องกางในกลุ่มโน้ต (เกิน 4–5 เฟร็ต = โทษหนัก) |
  | String skip/cross | การข้ามสายหลายสาย |
  | Open string | ชอบ/ไม่ชอบสายเปล่า (ตั้งค่าได้) |
  | High fret | เฟร็ตสูงมากเล่นยาก (เกิน ~15–17 มีโทษเพิ่ม) |
  | Position consistency | อยู่ใน position เดียวนานๆ ได้โบนัส |
  | Technique-friendly | โน้ตที่ทำ hammer/pull/slide ได้ลื่นได้โบนัส |
  | Repeat consistency | ท่อนที่ซ้ำกัน (เช่น chorus) ใช้ fingering เดียวกันเพื่อจำง่าย |
- ผลลัพธ์: **วิธีหลัก + ทางเลือก 2–3 แบบ** (เช่น "เล่นต่ำ/สูง", "ใช้สายเปล่าเยอะ") ให้กดสลับดู

### 8.3 Block Mode (โน้ตอยู่ในบริเวณที่กำหนด แต่กระจายทุกสาย)
**Block คืออะไร:** ช่วงบริเวณบนคอกีตาร์ที่ครอบคลุมทุกสาย ของ key ที่ตรวจได้ เช่น
- 7 diatonic positions (ท่าสเกล 3 โน้ต/สาย)
- 5 pentatonic boxes
- CAGED shapes
- Custom block: ผู้ใช้ลากกำหนดช่วงเฟร็ตเอง (เช่น เฟร็ต 5–9)

**การทำงาน**
1. ระบบ generate รายการ block ของ key ปัจจุบัน (เช่น A minor: Position 1–7, Box 1–5) แสดงเป็นแผนภาพ **fretboard** พร้อมจุดโน้ตของสเกล
2. ผู้ใช้ **เลือกได้หลาย block** (multi-select) — หรือเลือก block **แยกตามท่อน/ห้อง** (เช่น Verse ใช้ Block 2, Chorus ใช้ Block 3+4)
3. กด "สร้างแทป" → solver ใช้ candidate เฉพาะ (string, fret) ที่อยู่ใน union ของ block ที่เลือก
   - โน้ตกระจายทุกสายได้ตามปกติ แต่ **ไม่หลุดกรอบ block**
4. **Strict / Soft mode**
   - *Strict*: ห้ามหลุด block เด็ดขาด
   - *Soft*: หลุดได้แต่โดนโทษหนัก + ขึ้นเตือนสีแดงที่โน้ตนั้น
5. **Feasibility check ก่อนสร้าง** — แสดงรายงานว่า block ที่เลือกครอบคลุมเมโลดี้กี่ % เช่น "ครอบคลุม 94%, โน้ตต่ำกว่า block 6 ตัว (ห้อง 12, 27)"
6. ถ้ามีโน้ตที่ block ครอบคลุมไม่ถึง ให้ผู้ใช้เลือกวิธีจัดการ:
   - ขยับ octave เฉพาะตัวนั้น (octave fold)
   - ขยับเมโลดี้ทั้งเพลงขึ้น/ลง octave
   - ขยาย block ให้อัตโนมัติ (เพิ่ม 1–2 เฟร็ต)
   - ปล่อยตัวนั้นออกนอก block พร้อมเตือน
7. โน้ต chromatic นอก scale (accidental) อนุญาตให้อยู่ใน **ช่วงเฟร็ต** ของ block ได้แม้ไม่ใช่โน้ตใน shape เพื่อไม่ให้ทำนองเพี้ยน

### 8.4 Playability Engine (ถ้าโน้ตไกลกัน ให้หาทางที่ง่ายที่สุด)
เมื่อพบว่าโน้ตสองตัวติดกันห่างเกินไป (ตามกฎ stretch/shift ที่ผูกกับ tempo) ระบบจะลอง **ตามลำดับ**:
1. เปลี่ยนสาย/เฟร็ตของโน้ตเดียวกัน (pitch เดิม) เพื่อลดระยะ — **ไม่เปลี่ยน pitch**
2. ปรับ fingering ของโน้ตข้างเคียงเพื่อให้ chain ทั้งช่วงต่อกันลื่น
3. ใช้ technique ช่วย (slide, hammer/pull) ถ้าเหมาะ
4. ถ้ายังไม่ได้ → เสนอ octave displacement เฉพาะโน้ต (เป็น suggestion ไม่ทำเอง)
5. ติดป้ายระดับความยาก (🟢 ง่าย / 🟡 ปานกลาง / 🔴 ยาก) ต่อวลี + ต่อห้อง และสรุปความยากรวมทั้งเพลง

> หลักการ: **pitch ที่ถูกต้องสำคัญกว่าความง่ายเสมอ** — ระบบไม่เปลี่ยนโน้ตเพื่อให้เล่นง่ายโดยไม่บอก ถ้าต้องเปลี่ยน octave จะเป็นตัวเลือกที่ผู้ใช้ต้องยืนยัน

---

## 8B. Music Theory Layer (music21 + โมเดลคอร์ด)

ชั้นนี้อยู่ **หลัง** ขั้นตอนฟังเสียง (key/F0/chord) เพื่อทำให้ผลลัพธ์ถูกต้องตามทฤษฎีและอ่านง่าย ไม่ได้แทนที่การวิเคราะห์เสียง

### บทบาทของ music21
| งาน | ใช้ทำอะไร |
|---|---|
| **สะกดชื่อโน้ต/คอร์ดตาม key** | ใน F major ต้องเป็น `Bb` ไม่ใช่ `A#`; ใน E major ต้องเป็น `G#` ไม่ใช่ `Ab` → ป้ายชื่อบน piano roll, chord sheet และ tab อ่านถูกตามทฤษฎี |
| **สเกล / โหมด** | generate โน้ตของ major, natural/harmonic/melodic minor, pentatonic, modes → ใช้สร้างรายการ block ในหัวข้อ 8.3 |
| **Interval / Octave** | คำนวณระยะห่าง, ย้าย octave, ตรวจ range ของโน้ต |
| **Transpose** | ย้าย key ของเมโลดี้/คอร์ดทั้งเพลง → ใช้ในหัวข้อ 11 |
| **Key cross-check** | วิเคราะห์ key จาก "โน้ตเมโลดี้ที่แกะได้" แล้วเทียบกับ key จาก chroma ของเสียง ถ้าไม่ตรงกัน (เช่น relative major/minor สลับกัน) → เตือนผู้ใช้ให้ยืนยัน |
| **Roman numeral / scale degree** | แสดงคอร์ดและโน้ตแบบ I–IV–V, 1–7 ได้ |
| **Export MusicXML** | ส่งต่อไป MuseScore / Guitar Pro |

### สิ่งที่ music21 ทำไม่ได้ (ต้องเขียนเอง)
- **ไม่รู้เรื่อง capo, tuning, ความยากในการเล่น, fingering** → "key ที่เล่นง่าย" ใช้ cost function ของเราเองตามหัวข้อ 8.2 และ 11 โดย music21 ช่วยแค่คำนวณ transpose, ชื่อคอร์ด และชื่อโน้ต
- **ไม่ฟังเสียง** → ทำงานกับโน้ต/คอร์ดที่แกะเสร็จแล้วเท่านั้น
- **ค่อนข้างช้า** → เรียกในระดับเพลง/ท่อน ไม่เรียกทีละโน้ตในลูปหนัก (solver ของ tab ใช้ lookup table ของ pitch → (string, fret) ที่ precompute ไว้เอง)

### การเลือกโมเดลคอร์ด (ลำดับ)
1. **BTC** เป็นตัวหลัก — vocabulary กว้างกว่า major/minor (7th, maj7, sus, dim, aug ฯลฯ) ระบุเวลาได้ รันบน PyTorch + CUDA
2. **chroma + HMM/Viterbi (เขียนเอง)** เป็น fallback ถ้า BTC รันบน Windows/PyTorch ปัจจุบันไม่ได้ หรือเป็นตัวเทียบความเห็นตรงกัน
3. **ไม่ใช้ Autochord** — ตรวจหน้า PyPI แล้ว: ใช้โมเดล Bi-LSTM-CRF บน TensorFlow ต้องมี Vamp NNLS-Chroma plugin รองรับแค่ 25 คลาส (major 12, minor 12, no-chord) จึงทำ 7th/sus ไม่ได้ และรุ่นล่าสุดออกเมื่อ ต.ค. 2021
4. **ตัดสินด้วย benchmark set** — วัดคอร์ดของแต่ละตัวกับเพลงที่ผู้ใช้แกะไว้ (เช่น chord symbol recall ด้วย mir_eval) ตัวไหนแม่นกว่ากับเพลงแนวที่ผู้ใช้ฟังก็ใช้ตัวนั้นเป็นค่าเริ่มต้น
5. **เทียบแหล่งเสียงที่ป้อนให้โมเดลคอร์ด** — instrumental stem, mix ต้นฉบับ, และผลรวมสองแบบ เพราะการแยกเสียงอาจสร้าง artifact ที่ทำให้คอร์ดเพี้ยนได้ (วัดด้วย benchmark ไม่เดา)
6. ทางสำรอง chroma + template + Viterbi มักแม่นน้อยกว่าโมเดลเรียนรู้ลึกในคอร์ดซับซ้อนและ slash chord (ตามที่ทราบทั่วไป ยังไม่ได้วัดในโปรเจกต์นี้) ดังนั้นห้ามสรุปความแม่นยำก่อนวัดกับ benchmark

### ขั้นตอนหลังได้ผลคอร์ด (post-processing ด้วย music21)
1. **Beat-synchronous smoothing** — ไม่ให้คอร์ดเปลี่ยนกลางจังหวะแบบสุ่ม
2. **สะกดชื่อคอร์ดตาม key** (เช่น `Bb` ไม่ใช่ `A#`)
3. **ตรวจความสอดคล้องกับ key**: คอร์ดที่ไม่อยู่ใน key ให้ติดป้าย *borrowed/non-diatonic* และแสดงเป็น **คำเตือนเบาๆ** ไม่บังคับแก้ เพราะเพลงมี borrowed chord, secondary dominant, modal interchange ได้จริง
4. **ตรวจคอร์ดกับเมโลดี้**: โน้ตเมโลดี้ที่ตกลงบนคอร์ดนั้นเข้ากันไหม ถ้าไม่เข้าเลยให้ flag ให้ผู้ใช้ตรวจ (ช่วยจับทั้งคอร์ดพลาดและโน้ตพลาด)
5. **Simplify chord** (ตัวเลือก): ย่อคอร์ดซับซ้อนเป็นรูปที่เล่นง่าย (เช่น `Cmaj9` → `C`) สำหรับ chord sheet

### Key ที่ยืนยันแล้วเป็นศูนย์กลาง
- ค่า key (รวมช่วง modulation) ที่ผู้ใช้ยืนยันถูกส่งให้ทุกส่วนที่ต้องใช้: การ snap โน้ต (S7), การสะกดชื่อ, block generator, chord post-processing, key suggestion
- ผู้ใช้เปลี่ยน key → รัน stage ที่ได้รับผลกระทบใหม่เท่านั้น (ใช้ cache graph ตามหัวข้อ 13)

---

## 9. แปลงลูกเล่นเสียงร้อง → เทคนิคกีตาร์

ใช้ pitch contour ดิบ (จาก S5/S6) วิเคราะห์ภายในและระหว่างโน้ต แล้วเสนอเป็น **suggestion ที่ accept/reject ได้** (ค่า threshold ปรับได้ใน Settings; ค่าด้านล่างเป็นค่าเริ่มต้นที่ต้องจูนด้วยเพลงจริง)

| ลูกเล่นเสียงร้อง | วิธีตรวจ | เทคนิคกีตาร์ที่เสนอ |
|---|---|---|
| ไหลเสียงต่อเนื่องจากโน้ตหนึ่งไปอีกโน้ต (portamento) | pitch เปลี่ยนต่อเนื่องไม่มี gap/onset ใหม่ ระหว่างโน้ต | **Slide** (`/` ขึ้น, `\` ลง) |
| ต่อโน้ตนุ่มๆ ไม่มี attack ใหม่ ช่วงสั้นๆ ห่างกัน 1–2 semitone | ไม่มี onset energy ที่ชัดที่โน้ตที่สอง, interval เล็ก | **Hammer-on** (ขึ้น) / **Pull-off** (ลง) |
| เสียงไต่ขึ้นหาโน้ตเป้าหมายระหว่างเสียงยาว | pitch ค่อยๆ ขึ้น 1–2 semitone ภายในโน้ตเดียว | **Bend** (½, full, 1½) |
| เสียงสั่น (vibrato) | F0 แกว่งเป็นคาบ ~4–8 Hz, ความลึก ~20–100 cents | **Vibrato** (`~`) |
| เริ่มโน้ตจากต่ำกว่าแล้วไต่ขึ้นหาโน้ต (scoop) | ช่วงต้นโน้ตต่ำกว่าเป้าหมาย 50–200 cents แล้วขึ้นเร็ว | **Slide-in จากเฟร็ตล่าง** |
| ปลายโน้ตหล่น (fall-off) | pitch ตกลงท้ายโน้ต | **Slide-out ลง** |
| โน้ตสั้นๆ ก่อนโน้ตหลัก (ornament / grace) | โน้ตสั้นมาก < ~80ms ติดกับโน้ตหลัก | **Grace note** (hammer/slide) |
| เสียงเอื้อน/melisma (หลายโน้ตในพยางค์เดียว) | หลายโน้ตภายใต้พยางค์เดียวกันจาก lyrics alignment | **Legato run** (hammer/pull ต่อเนื่อง) |

- UI: แสดงเป็นไอคอนเล็กๆ บนโน้ต พร้อมแถบ confidence; ปุ่ม *Accept all / Reject all / ตรวจทีละตัว*
- ผู้ใช้เปิด/ปิดเทคนิคแต่ละชนิดแบบ global ได้ (เช่น ไม่เอา bend)
- เทคนิคต้อง **เล่นได้จริงบนตำแหน่งที่เลือก** (เช่น hammer-on ต้องอยู่สายเดียวกัน) — solver ตรวจให้ และปรับ fingering ให้รองรับเทคนิคนั้นถ้าจำเป็น

---

## 10. Tab Editor (คลิกแก้ได้ทุกตัวทันที)

หลักการ: **ทุกโน้ตแก้ได้อิสระ ไม่มีข้อจำกัดเรื่องลำดับ** (ไม่ต้องลบตัวหลังเพื่อย้อนไปแก้ตัวหน้า)

- **คลิกที่โน้ต** → เลือกทันที → พิมพ์เลขเฟร็ตใหม่, ใช้ลูกศรเลื่อนเฟร็ต/สาย, ลากย้ายตำแหน่งเวลา
- **Popup ข้างโน้ต (inspector):** เปลี่ยนสาย/เฟร็ต, ความยาวโน้ต, เทคนิค (slide / hammer / pull / bend / vibrato / palm mute / tie / dead note / harmonic), ลบ, copy/paste, duplicate
- **เลือกหลายตัว** (ลากกรอบ / Shift-click) → ย้าย/ลบ/ใส่เทคนิคพร้อมกัน, transpose ขึ้นลงทีละเฟร็ต/ทีละสาย
- **ตัวเลือกตำแหน่งอื่น** — คลิกโน้ตแล้วกด "เล่นตรงอื่นได้ไหม" จะเห็นรายการ (string, fret) อื่นที่ pitch เดียวกัน พร้อม cost
- **Re-solve เฉพาะช่วง** — เลือกห้อง 9–12 แล้วกด "คำนวณ fingering ใหม่เฉพาะตรงนี้" (โน้ตที่ผู้ใช้ล็อกไว้จะไม่ถูกแตะ)
- **Lock note 🔒** — ล็อกโน้ตที่แก้เองแล้ว กัน auto-solver ทับ
- **Undo/Redo** ไม่จำกัด (command pattern), เก็บ history ใน project
- เล่นเสียงตัวอย่างของโน้ตที่แก้ทันที, เล่นเฉพาะช่วงที่เลือก, loop
- แสดง **fretboard diagram** ไฮไลต์ตำแหน่งของโน้ตปัจจุบันและขอบเขต block ที่ใช้
- ตรวจ **Validation** ตลอดเวลา: เฟร็ตเกินคอ, pitch ไม่ตรงสาย, stretch เกิน, ชนกันในเวลาเดียวกัน → ขีดเส้นใต้เตือนสีแดง/เหลือง

**เทคนิคที่ทำให้แก้ได้ทุกตัวจริง:** ใช้ data model แบบ id ต่อโน้ต (Section 8.1) และ render ผ่าน layer ของเราเองที่ map ตำแหน่งบนจอ ↔ note id ทำให้ hit-test ได้ทุกตัว ส่วน alphaTab ใช้เป็น engine เรนเดอร์/เล่นเสียง/export

**Hit-test บน alphaTab (ตามเอกสาร alphaTab):**
1. ตั้ง `settings.core.includeNoteBounds = true` **ก่อน** สร้าง `AlphaTabApi` (ค่าเริ่มต้นปิด เพราะเก็บตำแหน่งโน้ตทีละตัวกินประสิทธิภาพ)
2. รอ event `renderFinished` แล้วอ่าน `api.renderer.boundsLookup`
3. คลิกที่ (x, y) → `lookup.getBeatAtPos(x, y)` แล้ว `lookup.getNoteAtPos(beat, x, y)` เพื่อหาโน้ตที่คลิก
4. สิ่งที่ได้คืนมาคือ Note ของ alphaTab เอง ไม่ใช่ `note.id` ของเรา → **ต้องทำตารางแมปเอง** (เช่น ตำแหน่ง beat + ลำดับโน้ต ↔ note id)
5. เมื่อผู้ใช้แก้โน้ต ต้องสร้าง score ใหม่แล้ว render ใหม่ → **ความเสี่ยงด้านความเร็ว** ต้องวัดกับเพลงยาว และพิจารณา render ทีละท่อน
6. ยังไม่ยืนยัน: ระบบพิกัดของ x, y และว่าต้องเปิด `enablePlayer` ด้วยหรือไม่ (เอกสารหน้า includeNoteBounds ไม่ได้ระบุ) → ทดสอบใน Phase 4 ก่อนออกแบบ editor เต็มรูปแบบ

---

## 11. แนะนำ Key ที่เล่นง่าย

ประเมิน **ทุก transposition (−6…+5 semitone) × capo (0–7) × tuning (Standard / Drop D / ½ step down)** แล้วให้คะแนน:

| เกณฑ์ | น้ำหนักตัวอย่าง |
|---|---|
| โน้ตเมโลดี้อยู่ในช่วงกีตาร์ที่เล่นสบาย (ไม่ต่ำกว่าสายเปล่า, ไม่สูงเกินเฟร็ตที่กำหนด) | สูง |
| ค่า cost รวมของ fingering (ใช้ solver ตัวเดียวกันกับ Section 8) | สูง |
| จำนวนโน้ตที่ใช้สายเปล่าได้ (ลื่น/กังวาน) | กลาง |
| ความง่ายของคอร์ด (รูปเปิด C G D A E Am Em ฯลฯ) | กลาง |
| จำนวนครั้ง/ระยะการเลื่อน position | กลาง |
| (ตัวเลือก) เหมาะกับช่วงเสียงของผู้ใช้ถ้าจะร้อง | ผู้ใช้ติ๊กเปิด |

- แสดงผลเป็นตารางอันดับ Top 5 พร้อมเหตุผลสั้นๆ ("Capo 2 เล่น Am-form ได้ใช้ open string 14 โน้ต")
- กด "ใช้ key นี้" → ระบบ transpose เมโลดี้+คอร์ด+tab ให้ และ (ถ้าต้องการ) ปรับ pitch ของ backing track ด้วย rubberband เพื่อเล่นตามได้
- ต้นฉบับยังเก็บไว้ ย้อนกลับได้เสมอ

---

## 12. Export ทีละท่อนเป็นรูป

- เลือกท่อนจาก Structure (Intro, Verse1, Chorus …) หรือเลือกช่วงห้องเอง / หลายท่อนพร้อมกัน (batch)
- **ตัวเลือก:** จำนวน bar ต่อบรรทัด · แสดง tab อย่างเดียว / tab+โน้ตมาตรฐาน · ใส่คอร์ด · ใส่เนื้อเพลง · ใส่เลขห้อง/BPM/key · ธีมสว่าง/มืด · พื้นหลังโปร่งใส · ขนาด/DPI (สูงสุด 300+)
- **Format:** PNG, SVG, PDF (และ zip รวมทุกท่อน)
- ตั้งชื่อไฟล์อัตโนมัติ เช่น `เพลง_02_Chorus.png`
- Pipeline: alphaTab → SVG → headless Chromium/resvg → PNG/PDF
- Format อื่นๆ: **MIDI**, **MusicXML**, **Guitar Pro (.gp)**, **alphaTex**

---

## 13. Project & Cache

### โครงสร้างโปรเจกต์
```
projects/
└─ <project_id>/
   ├─ project.json            # metadata, key/bpm/ts, ตั้งค่า, version
   ├─ audio/original.wav
   ├─ stems/vocals.wav, instrumental.wav, lead.wav, backing.wav
   ├─ analysis/ beats.json, chords.json, lyrics.json, structure.json, f0.npy
   ├─ melody/ auto.json, edits.json    # แยก auto กับที่ผู้ใช้แก้
   ├─ tab/    tab.json, history.sqlite # undo history
   ├─ exports/
   └─ cache/  (content-addressed)
```

### Cache
- Cache key = `hash(ไฟล์เสียง) + stage + model_name + model_version + params + pipeline_version`
- เปลี่ยนค่าที่ไม่เกี่ยวข้อง (เช่น เลือก block ใหม่) → **ไม่ต้องประมวลผลเสียงซ้ำ** แค่รัน tab solver ใหม่
- เปลี่ยน key ที่ยืนยันเอง → รัน S7 เป็นต้นไปเท่านั้น
- Dependency graph ของ stage → invalidate เฉพาะที่ได้รับผลกระทบ
- ปุ่มจัดการ cache: ดูขนาด, ล้างต่อโปรเจกต์/ทั้งหมด, จำกัดขนาดสูงสุด (LRU)

### การบันทึก
- **Autosave** ทุกครั้งที่แก้ + ก่อนปิด, สำรองเวอร์ชัน (snapshot) ย้อนกลับได้
- **ผลอัตโนมัติ (auto) กับการแก้ของผู้ใช้ (edits) เก็บแยกกัน** → รัน analysis ใหม่แล้วการแก้ของผู้ใช้ไม่หาย (merge ด้วย note id/lock)
- Import/Export project เป็นไฟล์ `.gnproj` (zip) ย้ายเครื่องได้
- หน้า Library: รายการโปรเจกต์/เพลงทั้งหมด ค้นหา แท็ก

---

## 14. Status & System Monitor

### แถบสถานะ (Status Bar ล่างจอ ตลอดเวลา)
```
[⚙ Stage 3/10: Separating vocals ████████░░ 78%  ETA 0:23]   GPU 92% · VRAM 5.8/8.0GB · CPU 41% · RAM 11.2/32GB   [Cancel]
```
- ชื่อ stage ปัจจุบัน + % + ETA + ปุ่ม Cancel
- **GPU util / VRAM / CPU / RAM** อัปเดตทุก ~500ms ผ่าน WebSocket (`pynvml` + `psutil`)
- **Heartbeat:** ถ้าไม่มี progress เกิน X วินาที จะแสดง "กำลังทำงาน..." พร้อม spinner และเวลาที่ผ่านไป เพื่อให้รู้ว่าไม่ค้าง
- **หน้า Job panel (กางออก):** รายการ stage ทั้งหมดพร้อมสถานะ (✓ เสร็จ / ⏳ กำลังทำ / ⏸ รอ / ⚠ ผิดพลาด) + เวลาที่ใช้ + log สด
- ข้อมูลเสริม: model ที่กำลังโหลด, cache hit/miss ของแต่ละ stage ("✓ จาก cache")
- แจ้งเตือนเมื่อเสร็จ (เสียง/notification), ผิดพลาด → ข้อความชัดเจน + ปุ่ม retry stage นั้น
- UI **ไม่บล็อก** ระหว่างประมวลผล (ใช้งานส่วนอื่นได้, งานรันใน worker แยก)
- เตือนทรัพยากร: VRAM > 90% / RAM > 85% → แนะนำลด preset

### Progress ที่เชื่อถือได้
- แต่ละ stage รายงาน progress เองเป็นช่วง (เช่น Demucs รายงานตาม chunk ที่เสร็จ) ไม่ใช่สุ่มเลขหลอก
- ETA คำนวณจากสถิติจริงของ stage นั้นในเครื่องนี้ (เก็บใน benchmark DB)

---

## 15. ความแม่นยำ (สิ่งที่ต้องเน้นที่สุด) — แผนรับประกัน "ตรงที่สุด"

1. **แยกเสียงคุณภาพสูง 2 ชั้น** (vocals → lead) ลดเสียงประสาน/เสียงเครื่องดนตรีรั่ว
2. **F0 ensemble** (RMVPE + CREPE) + แก้ octave error ด้วย Viterbi
3. **Key detection จาก instrumental** + ตรวจ tuning offset + modulation
4. **Key-aware แบบมีเงื่อนไข** (ไม่ snap มั่ว, คง accidental จริงไว้)
5. **Confidence ทุกโน้ต** + ไฮไลต์ตัวที่ต้องตรวจ → ผู้ใช้โฟกัสแก้เฉพาะจุดเสี่ยง
6. **A/B Verification Tools** — เล่นเมโลดี้สังเคราะห์ทับเสียงร้อง, overlay F0 contour, solo/mute stem
7. **ชุดทดสอบ (Benchmark set)** — ผู้ใช้แกะมือไว้ 10–20 เพลง (เก็บเป็น ground truth) แล้วให้ระบบวัดอัตโนมัติด้วย **mir_eval** (note-level F1, onset tolerance 50ms, raw pitch accuracy, chroma accuracy) ทุกครั้งที่เปลี่ยน model/ค่า → **ปรับแต่งด้วยตัวเลข ไม่ใช่ความรู้สึก** และป้องกัน regression
8. **เก็บการแก้ไขของผู้ใช้** (โน้ตไหนที่โปรแกรมพลาดแล้วแก้) เป็นข้อมูลวิเคราะห์ว่า stage ไหนพลาดบ่อย เพื่อปรับ threshold

> ข้อจำกัดที่ควรรู้ล่วงหน้า: เพลงที่เสียงร้องซ้อนทับเยอะ, เสียงร้อง effect หนัก, rap/สปีช, หรืออัดที่จูนเพี้ยนมาก จะยากกว่าปกติ — ระบบจะบอกผ่านค่า confidence ต่ำแทนที่จะแสดงผลมั่นใจเกินจริง

---

## 16. ฟีเจอร์เสริมที่แนะนำเพิ่ม (คุณถามว่า "เพิ่มไรอีกดีมั้ย")

ลำดับตามคุณค่า/ความคุ้ม:

| # | ฟีเจอร์ | ประโยชน์ |
|---|---|---|
| 1 | **Loop A–B + ชะลอความเร็ว 50–120% (ไม่เปลี่ยน pitch)** | ฝึกท่อนยากได้ทันที (คุ้มมาก, ทำง่าย) |
| 2 | **Backing track mode** (ตัดเสียงร้อง + slider ปรับดังเสียงร้อง) | เล่นกีตาร์ทับเพลงจริง |
| 3 | **Fretboard diagram สด** ไฮไลต์ตำแหน่งที่ต้องกด ณ ตอนนั้น + ขอบเขต block | มองภาพคอกีตาร์ง่าย |
| 4 | **Export MIDI / MusicXML / Guitar Pro** | ใช้ต่อใน DAW / Guitar Pro / MuseScore |
| 5 | **รองรับ tuning อื่น** (Drop D, Half-step down, DADGAD, Custom) | เพลงที่จูนไม่ standard |
| 6 | **เลขนิ้วมือซ้าย (fingering numbers 1–4)** บน tab | ซ้อมถูกท่า |
| 7 | **Harmony generator** (สร้างเมโลดี้ประสาน 3rd/6th) | แกะแล้วอยากเล่น duo |
| 8 | **ใช้ mic ฟังผู้ใช้เล่นแล้วตรวจ pitch/จังหวะเรียลไทม์** (practice grading) | ฝึกให้แม่น — ทำเป็น Phase ท้าย |
| 9 | **เปรียบเทียบเวอร์ชันของ tab** (diff) | ย้อนดูสิ่งที่แก้ |
| 10 | **Keyboard shortcuts ครบ + Command palette** | ทำงานเร็ว |
| 11 | **Playlist/Batch queue** | ใส่หลายเพลงแล้วปล่อยประมวลผลข้ามคืน |
| 12 | **Section-based block presets** (จำชุด block ที่ใช้บ่อยเป็น preset) | ตั้งค่าไวขึ้น |

---

## 17. API โดยสังเขป

```
POST /projects                      สร้างโปรเจกต์ (url หรือ upload)
GET  /projects, /projects/{id}      รายการ/รายละเอียด
POST /projects/{id}/analyze         เริ่ม pipeline (preset, override key/bpm ได้)
POST /projects/{id}/stages/{name}/rerun
POST /jobs/{id}/cancel
GET  /projects/{id}/melody|chords|beats|lyrics|structure
PUT  /projects/{id}/melody          บันทึกการแก้โน้ต
GET  /projects/{id}/blocks?key=Am   รายการ block ของ key
POST /projects/{id}/tab/generate    { blocks, mode(strict|soft), tuning, capo, weights, range }
GET|PATCH /projects/{id}/tab        อ่าน/แก้โน้ตทีละ id
POST /projects/{id}/tab/resolve     re-solve เฉพาะช่วง
POST /projects/{id}/keys/suggest    แนะนำ key ที่เล่นง่าย
POST /projects/{id}/export          { sections, format, options }
WS   /ws/status                     progress + system stats + log
```

---

## 18. โครงสร้างโค้ด (monorepo)

```
gracenote/
├─ backend/
│  ├─ app/ (api, jobs, orchestrator, cache, store, monitor)
│  ├─ pipeline/ (ingest, separate, f0, notes, key, beat, chord, lyrics, structure)
│  ├─ tab/ (candidates, solver, blocks, techniques, playability, keysuggest)
│  ├─ export/ (alphatex, musicxml, midi, gp, render)
│  └─ tests/ (unit, integration, benchmark/mir_eval)
├─ frontend/
│  ├─ src/ (pianoroll, chordsheet, tabeditor, player, metronome, status, library, export)
│  └─ ...
├─ benchmark/ (ground-truth + scripts)
├─ docs/
└─ plan.md
```

---

## 19. Roadmap (แบ่งเป็น Phase พร้อมเกณฑ์ผ่าน)

### Phase 0 — Setup & Benchmark (≈ 3–5 วัน)
- Setup บน **Windows ล้วน**: Python 3.10/3.11 + venv, PyTorch CUDA, ffmpeg, yt-dlp, Node.js
- **เช็กลิสต์ทดสอบการติดตั้งบน Windows** (ลองทีละตัว ผ่านแล้วติ๊ก):
  - [ ] `torch.cuda.is_available()` เป็น True และเห็น RTX 4060
  - [ ] Demucs / audio-separator แยกเสียงเพลงทดสอบได้บน GPU
  - [ ] RMVPE และ CREPE (torchcrepe) ให้ F0 ได้
  - [ ] faster-whisper (CUDA) ถอดเสียงได้ ไม่ติดปัญหา cuDNN DLL
  - [ ] beat_this ตรวจ beat/downbeat ได้
  - [ ] librosa chroma → key detection ทำงานได้
  - [ ] **BTC** รันบน PyTorch/CUDA ปัจจุบันของเครื่องได้ (ถ้าไม่ได้ → ใช้ chroma+HMM เป็นตัวหลักแทน)
  - [ ] **music21** ติดตั้งได้ และทดสอบการสะกดโน้ต/transpose/scale ได้ถูกต้อง
  - [ ] เทียบความแม่นยำคอร์ดของแต่ละโมเดล และเทียบแหล่งเสียง (instrumental stem vs mix) บน benchmark set แล้วเลือกตัวหลัก
  - [ ] `python scripts/check_env.py --deep` ผ่าน (ถอดเสียงจริงด้วย faster-whisper บน GPU; ต้องมีอินเทอร์เน็ตเพื่อโหลดโมเดล tiny)
  - [ ] yt-dlp โหลดจาก YouTube ได้, ffmpeg แปลงเป็น WAV ได้
  - [ ] Playwright (Chromium) render SVG → PNG ได้
  - [ ] `start.bat` เปิด backend + เบราว์เซอร์ได้
- ถ้าตัวไหนไม่ผ่าน → หาตัวแทน หรือย้ายเฉพาะ stage นั้นไป WSL2 (ทางสุดท้าย)
- ทดสอบแต่ละ model บนเครื่องนี้: เวลา, VRAM, คุณภาพ
- เตรียม **benchmark set** 10–20 เพลง + ground truth ที่แกะมือ
- ✅ เกณฑ์ผ่าน: รู้เวลา/VRAM จริงของทุก stage, มี script วัด mir_eval ใช้งานได้

### Phase 1 — MVP: เสียง → Piano Roll (≈ 2 สัปดาห์)
- ingest + separation + F0 + note segmentation + key-aware snap
- Piano roll พร้อมชื่อโน้ต/octave, player, A/B verification
- Status bar พื้นฐาน (progress + CPU/GPU/RAM)
- ✅ เกณฑ์ผ่าน: เพลงทดสอบแกะได้โน้ตตรงตาม ground truth ตามเป้า F1 ที่ตั้งไว้ (กำหนดหลังได้ baseline จาก Phase 0)

### Phase 2 — Analysis ครบ (≈ 2 สัปดาห์)
- key/modulation, tempo/beat/time signature, chords, lyrics+alignment, structure
- Chord sheet view + metronome ตาม beat grid
- ✅ เกณฑ์ผ่าน: คอร์ดและ beat ตรงกับเพลงทดสอบ, metronome เคาะตรงจังหวะฟังแล้วไม่เพี้ยน

### Phase 3 — Guitar Tab + Block + Playability (≈ 2–3 สัปดาห์)
- fingering solver (DP), block generator, strict/soft mode, feasibility report
- playability engine + ระดับความยาก
- render tab ด้วย alphaTab + เล่นเสียงตัวอย่าง
- ✅ เกณฑ์ผ่าน: เลือก block แล้วโน้ตไม่หลุดกรอบ (strict), ทดลองกับเพลงจริงแล้วเล่นได้โดยแก้น้อย

### Phase 4 — Tab Editor (≈ 2 สัปดาห์)
- คลิกแก้ได้ทุกตัว, multi-select, inspector, lock, re-solve ช่วง, undo/redo, validation
- ✅ เกณฑ์ผ่าน: แก้โน้ตใดๆ ก็ได้ด้วยการคลิกตรงนั้น ไม่ต้องลบย้อน, undo/redo ถูกต้อง

### Phase 5 — เทคนิคกีตาร์จากเสียงร้อง + Key Suggestion (≈ 1–2 สัปดาห์)
- ตรวจ slide/hammer/pull/bend/vibrato/scoop/fall + UI accept/reject
- ระบบแนะนำ key/capo/tuning ที่เล่นง่าย
- ✅ เกณฑ์ผ่าน: suggestion ส่วนใหญ่สมเหตุสมผลกับเพลงทดสอบ, ปิดเปิดเทคนิคได้

### Phase 6 — Export + Project/Cache + Status เต็มรูปแบบ (≈ 1–2 สัปดาห์)
- export ทีละท่อน PNG/SVG/PDF + MIDI/MusicXML/GP
- project save/load, autosave, cache graph, library
- Job panel เต็ม, heartbeat, ETA, ยกเลิกงาน
- ✅ เกณฑ์ผ่าน: เปิดโปรเจกต์เดิมแล้วไม่ต้องประมวลผลซ้ำ, export รูปคมชัดครบทุกท่อน

### Phase 7 — Polish & ฟีเจอร์เสริม (ต่อเนื่อง)
- loop/ชะลอความเร็ว, backing track, fretboard diagram, tuning อื่น, shortcuts
- ปรับ performance รอบสุดท้าย (ONNX/TensorRT ถ้าคุ้ม)
- (ทางเลือก) แพ็กเป็นแอปเดสก์ท็อปด้วย Tauri

> ระยะเวลาเป็นประมาณการสำหรับนักพัฒนา 1 คนทำเต็มเวลา ปรับได้ตามจริง

---

## 20. ความเสี่ยง & วิธีรับมือ

| ความเสี่ยง | ผลกระทบ | วิธีรับมือ |
|---|---|---|
| เสียงร้องซ้อน/effect/ประสานหนัก ทำ F0 พลาด | โน้ตผิด | แยก lead, ensemble F0, confidence + A/B tool |
| Octave error | โน้ตกระโดดผิด octave | Viterbi smoothing, เทียบกับ key/range |
| VRAM 8GB ไม่พอกับ model ใหญ่ | crash | รันเรียงทีละ model, fp16, chunking, ปล่อย VRAM ทุก stage, preset |
| library ดนตรีบางตัวลงบน Windows ไม่ได้ | เสียเวลา | เลือกตัวที่ลงบน Windows ได้ตั้งแต่ต้น (beat_this, librosa) + เช็กลิสต์ Phase 0 + stage อยู่หลัง interface เดียวกัน; WSL2 เป็นทางสุดท้ายเฉพาะ stage ที่จำเป็น |
| Lyrics ภาษาไทยจัดคำไม่แม่น | chord sheet คลาดตำแหน่ง | ตัดคำด้วย PyThaiNLP, ให้วางเนื้อเองแล้ว align, แก้ตำแหน่งด้วยมือได้ |
| Chord detection ไม่แม่นในเพลงซับซ้อน | คอร์ดผิด | ensemble + beat-sync smoothing + แก้ไขได้ในหน้า chord sheet |
| Tab solver ให้ผลไม่ถูกใจ | ต้องแก้เยอะ | ปรับน้ำหนัก cost ใน Settings, มีหลายทางเลือก, re-solve เฉพาะช่วง |
| ปัญหาลิขสิทธิ์/ToS ของ YouTube | ข้อกฎหมาย | ใช้ส่วนตัวเพื่อการศึกษา/ฝึกซ้อม, เก็บไฟล์ในเครื่อง ไม่เผยแพร่ซ้ำ |

---

## 21. สิ่งที่ต้องตัดสินใจก่อนเริ่ม (Open Questions)

1. ~~รัน backend แบบ Windows native หรือ WSL2?~~ → **ตัดสินใจแล้ว: Windows ล้วน + local web app** (WSL2 สำรองเฉพาะกรณีจำเป็น)
2. เพลงส่วนใหญ่เป็น **ไทย / อังกฤษ / ผสม**? (กระทบการเลือก model ถอดเนื้อ)
3. เล่นกีตาร์ **standard tuning** ตลอดไหม? มี 7 สาย/ใช้ capo บ่อยไหม?
4. ต้องการ **แอปเดสก์ท็อป** หรือเปิดผ่านเบราว์เซอร์ localhost พอ?
5. รูปแบบ export รูปที่ชอบ (ขนาด, ธีม, จำนวน bar ต่อบรรทัด) เพื่อกำหนดค่าเริ่มต้น
6. อยากให้ tab แสดง **tab อย่างเดียว** หรือ tab + โน้ตมาตรฐาน?

---

## 22. Definition of Done (ภาพรวม)

- [ ] ใส่ลิงก์ YouTube/ไฟล์เสียง → ได้ piano roll เมโลดี้พร้อมชื่อโน้ต+octave ภายในไม่กี่นาที
- [ ] ตรวจ key / BPM / time signature / คอร์ด / เนื้อเพลง ได้ และแก้ไขเองได้
- [ ] Chord sheet (คอร์ดบน เนื้อล่าง) + metronome เคาะตรง beat จริง
- [ ] สร้าง tab อัตโนมัติ เลือก block ได้ โน้ตไม่หลุดกรอบ กระจายทุกสาย
- [ ] Playability engine หาวิธีเล่นง่ายสุดโดย pitch ยังถูกต้อง
- [ ] แปลงลูกเล่นเสียงร้องเป็นเทคนิคกีตาร์ (accept/reject)
- [ ] คลิกแก้โน้ตใน tab ได้ทุกตัวโดยตรง + undo/redo
- [ ] แนะนำ key/capo ที่เล่นง่าย
- [ ] Export ทีละท่อนเป็นรูป + MIDI/MusicXML/GP
- [ ] บันทึกโปรเจกต์ + cache ไม่ประมวลผลซ้ำโดยไม่จำเป็น
- [ ] Status bar แสดง stage, %, ETA, GPU/VRAM/CPU/RAM และไม่ค้างโดยไม่บอก
- [ ] วัดความแม่นยำด้วย benchmark set (mir_eval) และไม่ regress

---

## 23. Engineering & Portfolio

โปรเจกต์นี้ใช้เป็น **portfolio project** ด้วย จึงทำตามหลักวิศวกรรมซอฟต์แวร์ตั้งแต่ต้น (รายละเอียดอยู่ในไฟล์แยก ไม่ซ้ำที่นี่):

| เรื่อง | ไฟล์ |
|---|---|
| กฎที่ Claude Code อ่านทุก session (สั้น) | `CLAUDE.md` |
| มาตรฐานวิศวกรรมแบบละเอียด (layers, testing, git, CI, Definition of Done, portfolio checklist) | `docs/ENGINEERING.md` |
| บันทึกการตัดสินใจเชิงสถาปัตยกรรม (ADR) | `docs/adr/` |
| ข้อความ `/goal` สำเร็จรูปของแต่ละ Phase | `docs/GOALS.md` |
| สคริปต์เช็กการติดตั้ง Phase 0 | `scripts/check_env.py` |
| CI (lint + test บน Windows) | `.github/workflows/ci.yml` |

หลักสำคัญ: เทสต์ที่ไม่ใช้ GPU รันใน CI ได้, เทสต์ที่ต้องใช้ GPU/โมเดลหนัก mark `gpu` และรันบนเครื่องผู้พัฒนา, ความแม่นยำของ pipeline วัดด้วย benchmark (mir_eval) ทุกครั้งที่แก้, ไม่ commit ไฟล์เสียง/โมเดล/ผลลัพธ์ที่มีลิขสิทธิ์
