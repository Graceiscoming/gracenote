---
description: Run the Phase 0 environment check on the user's Windows machine and explain every failing item with a concrete fix
disable-model-invocation: true
---

Run `python scripts/check_env.py --deep` and show the full output. The `--deep` flag really transcribes a short clip with faster-whisper on the GPU, so it needs internet the first time (downloads the small `tiny` model). If the user is offline, run it without `--deep` and say the Whisper GPU check was skipped.

For each line marked FAIL or WARN:

1. Say what it means in one sentence (Thai).
2. Give the exact fix (command or setting), using the hints in the output and plan.md section 4 and the Phase 0 checklist.
3. If a library cannot be installed on Windows, propose a replacement that does install there, or the WSL2 fallback for that single stage only. Do not move the whole project to Linux.

Rules:

- Never edit `scripts/check_env.py` to make a check pass.
- Do not claim anything works on the user's GPU unless the output shows it.
- End with a short list: what passed, what still needs the user's action, what is manual (BTC model, RMVPE weights).
