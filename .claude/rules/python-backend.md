---
paths:
  - "backend/**/*.py"
  - "scripts/**/*.py"
---

# Python backend rules

- Type hints on every public function; data crossing module boundaries uses pydantic models, not bare dicts
- `pipeline/` and `tab/` are pure domain code: never import FastAPI, never touch HTTP types
- Each pipeline stage implements the common stage interface (see docs/adr/0002) and declares its name, version and params so it can be cached
- GPU models: load lazily, run one at a time, release VRAM when the stage ends (`del model` + `torch.cuda.empty_cache()`)
- Thresholds and cost weights come from config, never literals inside algorithms
- Windows CUDA DLLs: call `app.windows_dll.add_nvidia_dll_dirs()` before the first import of `faster_whisper` or `ctranslate2` (CTranslate2 4.5+ needs cuDNN 9)
- Note segmentation combines several signals; lyric word boundaries are only a soft hint (docs/adr/0004)
- Never swallow exceptions silently; log with context (stage, project id, input hash)
- Use `pathlib.Path`; assume paths may contain Thai characters and spaces
- New logic gets a unit test in `tests/unit/`; anything needing CUDA or large models is marked `@pytest.mark.gpu`
