# Changelog

All notable changes are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/), versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Project skeleton: plan, CLAUDE.md, engineering standards, ADRs, CI, environment check script.
- `check_env.py --deep`: real faster-whisper transcription on the GPU to catch cuDNN/cuBLAS DLL problems.
- `app.windows_dll.add_nvidia_dll_dirs()`: makes pip-installed NVIDIA DLLs visible on Windows before faster-whisper loads.
- ADR 0004: note segmentation from multiple signals.

### Changed
- Autochord dropped from the plan (TensorFlow + Vamp plugin, major/minor only, last release 2021).
- cuDNN pinned to 9.x in requirements.txt (CTranslate2 4.5+).
