---
description: Create a new Architecture Decision Record in docs/adr from the template
disable-model-invocation: true
argument-hint: <short-title>
---

Create a new ADR for: $ARGUMENTS

1. List `docs/adr/` and pick the next free number (zero-padded to 4 digits).
2. Copy `docs/adr/0000-template.md` to `docs/adr/<number>-<kebab-case-title>.md`.
3. Fill in Context, Decision, Alternatives considered and Consequences from the current conversation and code. Ask the user if the decision or its reasons are unclear. Do not invent reasons.
4. Set Status to `Proposed` unless the user says it is accepted, and use today's date.
5. If the ADR supersedes an older one, update the older ADR's status to `Superseded by <number>`.
6. Mention the new ADR in the commit message of the change it belongs to.
