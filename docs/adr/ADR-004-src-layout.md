# ADR-004 — Use src Layout for Python Packaging

## Status

Accepted

---

## Context

The project requires:

- reproducible imports
- reliable CI behavior
- proper package isolation
- compatibility with modern Python tooling
- prevention of accidental local imports

Flat repository layouts can introduce:

- hidden import errors
- inconsistent execution behavior
- CI/local environment mismatches

Scientific Python projects are especially vulnerable to:
- notebook path pollution
- implicit relative imports
- environment inconsistencies

---

## Decision

Adopt the `src/` layout pattern.

Project structure:

```text
src/
└── bci_calib/
