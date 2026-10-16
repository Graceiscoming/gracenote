# benchmark/

Measures how accurate the melody transcriber is, using songs you transcribed by hand.

## Ground truth format

One CSV per song in `ground_truth/`, named after the song (`song-name.csv`), one row per sung note:

```
onset_sec,offset_sec,midi_pitch
12.340,12.810,64
12.810,13.200,66
```

- `midi_pitch` is the sounding pitch (middle C = 60), not the guitar-written octave.
- Keep the matching audio in `benchmark/audio/` (git-ignored) with the same base name.

## Rules

- Ground truth is never edited to make a score go up.
- Metrics: note-level precision, recall and F1 with 50 ms onset tolerance (mir_eval), plus raw pitch accuracy.
- Results are saved to `docs/BENCHMARK.md` with the date, the pipeline version and the number of songs.

`run.py` is created in Phase 0.
