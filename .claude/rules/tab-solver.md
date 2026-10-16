---
paths:
  - "backend/tab/**/*.py"
  - "tests/**/test_tab*.py"
---

# Tab solver rules

- The pitch of a note is never changed by the solver. Only (string, fret) may change. Octave moves are suggestions that need user confirmation
- Fingering is a Viterbi / dynamic-programming search over candidate (string, fret) per note; the cost terms and weights are listed in plan.md section 8.2 and live in config
- Block Mode: candidates are restricted to the union of the selected blocks. Strict mode never leaves the blocks; soft mode allows it with a heavy penalty and a visible warning on the note
- Run a feasibility check before solving and report block coverage (percent of notes reachable)
- Notes the user edited or locked are fixed constraints for the solver, never overwritten by a re-solve
- Hand shift cost scales with tempo: fast passages punish big shifts harder
- Every solver rule needs a unit test with a tiny hand-written melody and an expected tab; prefer test-first
- Use music21 only for naming/transposing at song level, never inside the solver's inner loop (precompute a pitch -> (string, fret) table)
