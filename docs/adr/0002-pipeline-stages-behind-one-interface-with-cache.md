# ADR 0002: Pipeline stages behind one interface, with content-addressed cache

- Status: Accepted
- Date: 2026-10-16

## Context

The pipeline has many stages (ingest, separation, key, beat, F0, notes, chords, lyrics, structure). Models and libraries will change, some may not install on Windows, and heavy stages must not re-run when nothing relevant changed. Accuracy has to be measured per stage.

## Decision

Every stage implements one small interface: a name, a version, declared parameters, typed inputs and outputs, and a `run` method. The orchestrator computes a cache key from `hash(input audio) + stage name + stage version + model name/version + params + pipeline version` and skips the stage on a cache hit. Stages form a dependency graph so changing one input only invalidates the stages that depend on it.

User edits and automatic results are stored separately and merged at read time, so re-running a stage never overwrites user work.

## Alternatives considered

- One big script with functions: faster to start, but no caching, no swapping, no per-stage benchmark.
- A workflow engine (Airflow, Prefect): too heavy for a single-user local tool.

## Consequences

- Swapping a model means writing one new stage implementation and bumping its version.
- Every stage can be unit-tested with small synthetic inputs and benchmarked alone.
- GPU stages are scheduled one at a time by the orchestrator, which also frees VRAM between them.
- Small extra upfront cost: a stage base class, cache manager and tests in Phase 1.
