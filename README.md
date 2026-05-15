# BCI-Calib

🇧🇷 Português: [README.pt-BR.md](README.pt-BR.md)

[![CI](https://github.com/Frausino/bci-calib/actions/workflows/ci.yml/badge.svg)](https://github.com/Frausino/bci-calib/actions)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![SBOM: CycloneDX](https://img.shields.io/badge/SBOM-CycloneDX-informational)](https://cyclonedx.org)

Adaptive probabilistic calibration framework for multimodal Brain-Computer Interface (BCI) systems using EEG and autonomic physiological state modulation via HRV.

This project investigates whether autonomic nervous system dynamics can improve confidence calibration in motor imagery classifiers through dynamic temperature scaling modulated by physiological signals derived from Heart Rate Variability (HRV).

The repository is designed as a reproducible research engineering platform integrating:

- probabilistic calibration
- EEG signal processing
- HRV physiological modulation
- experiment tracking
- DevSecOps
- Clean Architecture
- deterministic ML pipelines

PIC IAR/CEUB 2026–2027.

---

# Research Hypothesis

Traditional calibration methods assume static confidence distributions during inference.

This project investigates whether calibration quality can be improved by dynamically adapting temperature scaling according to autonomic nervous system state estimated from HRV signals.

Central formulation:

```math
\tau(r_t) = 1 + (\tau_{max} - 1)\sigma(a r_t)
```

where:

- \(r_t\) = normalized autonomic state derived from RMSSD
- \(\sigma\) = sigmoid activation
- \(\tau\) = dynamic calibration temperature

Normalized physiological state:

```math
r_t = \frac{RMSSD_{smooth,t} - \mu_{train}}{\sigma_{train}}
```

Main evaluation metrics:

- Expected Calibration Error (ECE)
- Brier Score
- Calibration Curves
- Negative Log Likelihood (NLL)

---

# System Architecture

The repository follows Clean Architecture principles to isolate:

- scientific domain logic
- experiment orchestration
- infrastructure adapters
- presentation interfaces

```text
src/bci_calib/
├── domain/           # Pure scientific rules and calibration logic
├── application/      # Use-cases and orchestration
├── infrastructure/   # External integrations and adapters
└── presentation/     # CLI/API interfaces
```

## Architectural Goals

- reproducibility
- modular experimentation
- framework isolation
- deterministic environments
- maintainability
- scientific traceability

---

# Repository Structure

```text
bci-calib/
├── .github/              # CI/CD workflows
├── docs/                 # Governance and architecture docs
│   └── adr/              # Architecture Decision Records
├── logbook/              # Experimental tracking
├── model-cards/          # Model governance documentation
├── notebooks/            # Exploratory analysis only
├── results/              # Experimental outputs
├── src/                  # Main source code
├── tests/                # Automated tests
├── DAY_PROTOCOL.md       # Daily operational workflow
├── SECURITY.md           # Security policy
├── justfile              # Operational command runner
├── pyproject.toml
└── uv.lock
```

---

# Research Engineering Stack

| Layer                  | Technology     |
| ---------------------- | -------------- |
| Environment Management | uv             |
| Packaging              | Hatchling      |
| Linting                | Ruff           |
| Formatting             | Ruff Format    |
| Type Safety            | mypy strict    |
| Testing                | pytest         |
| Security SAST          | bandit         |
| Secret Scanning        | gitleaks       |
| Dependency Audit       | pip-audit      |
| SBOM                   | CycloneDX      |
| Experiment Tracking    | MLflow         |
| CI/CD                  | GitHub Actions |

---

# Setup

## Install uv

```bash
pip install uv
```

## Clone repository

```bash
git clone https://github.com/Frausino/bci-calib.git
cd bci-calib
```

## Synchronize environment

```bash
uv sync --all-extras
```

## Install pre-commit hooks

```bash
uv run pre-commit install
```

---

# Development Workflow

Operational workflow documentation:

```text
DAY_PROTOCOL.md
```

Architecture decisions:

```text
docs/adr/
```

Security policy:

```text
SECURITY.md
```

---

# Justfile Commands

## Synchronize dependencies

```bash
just sync
```

## Run Ruff lint

```bash
just lint
```

## Auto-fix lint issues

```bash
just fix
```

## Format code

```bash
just format
```

## Run type checking

```bash
just typecheck
```

## Run tests

```bash
just test
```

## Run security analysis

```bash
just security
```

## Audit dependencies

```bash
just audit
```

## Generate SBOM

```bash
just sbom
```

## Run complete validation pipeline

```bash
just all
```

## Start MLflow UI

```bash
just mlflow-ui
```

---

# Scientific Validation Protocol

All calibration modifications must evaluate:

| Metric            | Purpose                           |
| ----------------- | --------------------------------- |
| ECE               | Confidence calibration quality    |
| Brier Score       | Probabilistic prediction accuracy |
| Calibration Curve | Reliability visualization         |
| NLL               | Probabilistic uncertainty quality |

---

# Experiment Tracking

Experiments are tracked using MLflow.

Tracked artifacts include:

- hyperparameters
- calibration metrics
- preprocessing parameters
- model outputs
- evaluation curves
- experiment metadata

Future integration roadmap includes:

- benchmark dashboards
- experiment lineage
- comparative calibration studies

---

# Governance

## Architecture Decisions

Documented in:

```text
docs/adr/
```

## Security

See:

```text
SECURITY.md
```

## Research Reproducibility

Operational standards are defined in:

```text
DAY_PROTOCOL.md
```

---

# DevSecOps

| Area              | Tool           |
| ----------------- | -------------- |
| Static Analysis   | Ruff           |
| Security Analysis | bandit         |
| Secret Detection  | gitleaks       |
| Dependency Audit  | pip-audit      |
| SBOM Generation   | CycloneDX      |
| CI Validation     | GitHub Actions |

---

# Roadmap

| Phase    | Objective                                     | Status      |
| -------- | --------------------------------------------- | ----------- |
| Phase 1  | Infrastructure and governance                 | In Progress |
| Phase 2A | Synthetic benchmark pipeline                  | Planned     |
| Phase 2B | Experimental physiological collection         | Planned     |
| Phase 3  | Scientific manuscript and platform validation | Planned     |

---

# References

## Calibration

- Guo et al. (2017) — On Calibration of Modern Neural Networks

## BCI and Riemannian Geometry

- Barachant et al. (2012) — Multiclass Brain-Computer Interface Classification by Riemannian Geometry

## HRV Physiology

- Shaffer & Ginsberg (2017) — An Overview of Heart Rate Variability Metrics and Norms

## Benchmarking

- Chevallier et al. (2024) — MOABB: Trustworthy Algorithm Benchmarking for BCIs

---

# Disclaimer

This repository is:

- research software
- not certified medical software
- not intended for clinical diagnosis or treatment

No identifiable participant physiological data is distributed in this repository.

All future human-subject experiments must comply with:

- LGPD
- institutional ethics approval
- anonymization requirements

---

# License

MIT License.

Experiments are tracked using MLflow.

Tracked artifacts include:

- hyperparameters
- calibration metrics
- preprocessing parameters
- model outputs
- evaluation curves
- experiment metadata

Future integration roadmap includes:

- benchmark dashboards
- experiment lineage
- comparative calibration studies

---

# Governance

## Architecture Decisions

Documented in:

```text
docs/adr/
```

## Security

See:

```text
SECURITY.md
```

## Research Reproducibility

Operational standards are defined in:

```text
DAY_PROTOCOL.md
```

---

# DevSecOps

| Area              | Tool           |
| ----------------- | -------------- |
| Static Analysis   | Ruff           |
| Security Analysis | bandit         |
| Secret Detection  | gitleaks       |
| Dependency Audit  | pip-audit      |
| SBOM Generation   | CycloneDX      |
| CI Validation     | GitHub Actions |

---

# Roadmap

| Phase    | Objective                                     | Status      |
| -------- | --------------------------------------------- | ----------- |
| Phase 1  | Infrastructure and governance                 | In Progress |
| Phase 2A | Synthetic benchmark pipeline                  | Planned     |
| Phase 2B | Experimental physiological collection         | Planned     |
| Phase 3  | Scientific manuscript and platform validation | Planned     |

---

# References

## Calibration

- Guo et al. (2017) — On Calibration of Modern Neural Networks

## BCI and Riemannian Geometry

- Barachant et al. (2012) — Multiclass Brain-Computer Interface Classification by Riemannian Geometry

## HRV Physiology

- Shaffer & Ginsberg (2017) — An Overview of Heart Rate Variability Metrics and Norms

## Benchmarking

- Chevallier et al. (2024) — MOABB: Trustworthy Algorithm Benchmarking for BCIs

---

# Disclaimer

This repository is:

- research software
- not certified medical software
- not intended for clinical diagnosis or treatment

No identifiable participant physiological data is distributed in this repository.

All future human-subject experiments must comply with:

- LGPD
- institutional ethics approval
- anonymization requirements

---

# License

MIT License.

