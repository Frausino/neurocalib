# ADR-001 — Use uv for dependency management

## Status
Accepted

## Context

The project requires:
- deterministic environments
- fast CI synchronization
- cross-platform compatibility
- lockfile reproducibility

Traditional pip + requirements.txt presented:
- slower dependency resolution
- weaker reproducibility
- fragmented tooling

## Decision

Adopt uv as:
- package manager
- virtual environment manager
- lockfile generator

## Consequences

Positive:
- faster CI
- deterministic environments
- simplified onboarding

Negative:
- newer ecosystem tooling
- smaller community than pip
