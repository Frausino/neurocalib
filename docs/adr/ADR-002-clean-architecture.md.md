# ADR-002 — Adopt Clean Architecture

## Status

Accepted

---

## Context

The project integrates:

- EEG (Electroencephalography)
- HRV (Heart Rate Variability)
- probabilistic calibration
- physiological signal processing
- machine learning inference
- experiment tracking
- API/CLI interfaces

The system must support:

- reproducible scientific experiments
- modular ML pipelines
- future clinical integrations
- benchmarking across datasets
- independent testing of domain logic
- long-term maintainability

Direct coupling between:
- infrastructure,
- ML frameworks,
- APIs,
- experimental code

would increase technical debt and reduce reproducibility.

---

## Decision

Adopt Clean Architecture as the primary architectural pattern.

Project structure:

```text
src/bci_calib/
├── domain/
├── application/
├── infrastructure/
└── presentation/
