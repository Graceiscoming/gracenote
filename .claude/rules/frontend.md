---
paths:
  - "frontend/src/**"
---

# Frontend rules

- React + TypeScript (strict mode) + Vite; state with Zustand
- Piano roll draws on Canvas/WebGL (PixiJS), not DOM nodes per note
- The tab editor must let the user click any single note and edit it directly. Never require deleting later notes first
- Every note has a stable id; hit-testing maps screen position to note id
- alphaTab hit-testing: set `settings.core.includeNoteBounds = true` before creating the API, wait for `renderFinished`, then use `api.renderer.boundsLookup` (`getBeatAtPos`, then `getNoteAtPos`). It returns alphaTab's own Note objects, so keep our own table mapping them to our note ids
- Re-rendering after every edit may be slow on long songs: measure it, and render per section if needed. Whether `enablePlayer` is required for bounds and the x/y coordinate space are not confirmed yet, so verify in Phase 4 before building on them
- Undo/redo uses the command pattern and covers every edit
- Metronome runs in an AudioWorklet and follows the detected beat grid, not a fixed BPM
- The status bar always shows current stage, percent, ETA, GPU/VRAM/CPU/RAM, and a heartbeat so the app never looks frozen
- UI text is Thai first (note names switchable between C D E and โด เร มี); code, comments and identifiers are English
