# bci-calib

[![CI](https://github.com/Frausino/bci-calib/actions/workflows/ci.yml/badge.svg)](https://github.com/Frausino/bci-calib/actions)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![SBOM: CycloneDX](https://img.shields.io/badge/SBOM-CycloneDX-informational)](https://cyclonedx.org)

**Calibração Probabilística Dependente do Estado Autonômico com EEG e HRV**

PIC IAR/CEUB 2026–2027. OSF Pre-registration: _link publicado em S4 (ago/2026)._

---

## Sobre o projeto

Sistema de BCI (Brain-Computer Interface) que integra sinais de EEG e HRV para
calibração probabilística de classificadores de imaginação motora via temperatura
dinâmica τ(r_t) modulada por RMSSD.

Equação central:

```
τ(r_t) = 1 + (τ_max − 1) · σ(a · r_t)
```

onde r_t = (RMSSD_smooth_t − μ_train) / σ_train e σ é a função sigmoide.

---

## Arquitetura

Padrão Clean Architecture (Uncle Bob):

```
src/bci_calib/
├── domain/           # regras puras — zero dependências externas
├── application/      # casos de uso e orquestração
├── infrastructure/   # adaptadores externos (MOABB, Polar H10, MLflow)
└── presentation/     # CLI e API
```

---

## Setup

```bash
# Instalar uv (gerenciador de pacotes)
pip install uv

# Clonar e sincronizar dependências
git clone https://github.com/Frausino/bci-calib.git
cd bci-calib
uv sync --all-extras
pre-commit install
```

---

## Uso rápido

```powershell
# lint + test — GO/NO-GO check
uv run pre-commit run --all-files
uv run pytest --cov=src --cov-report=term-missing -q

# MLflow UI em localhost:5000
uv run mlflow ui --port 5000

# SBOM CycloneDX local
uv run cyclonedx-py environment --output-format JSON -o sbom.json
```

> Em Linux/macOS: `make all`, `make test`, `make mlflow-ui` (requer `make` instalado).

## DevSecOps

| Camada             | Ferramenta               |
| ------------------ | ------------------------ |
| SAST               | bandit                   |
| Secret scanning    | gitleaks                 |
| SCA (dependências) | pip-audit                |
| SBOM               | CycloneDX (gerado no CI) |
| Qualidade          | ruff + mypy strict       |

---

## Cronograma

| Fase                            | Período           | Status       |
| ------------------------------- | ----------------- | ------------ |
| Fase 1 — Infraestrutura e Ética | ago–set/2026      | em andamento |
| Fase 2A — Benchmark sintético   | out/2026–jan/2027 | pendente     |
| Fase 2B — Coleta experimental   | fev–mai/2027      | pendente     |
| Fase 3 — Manuscrito e produto   | jun–jul/2027      | pendente     |

---

## Referências principais

- Guo et al. (2017) — ECE e temperature scaling
- Barachant et al. (2012) — Geometria Riemanniana para BCI
- Shaffer & Ginsberg (2017) — RMSSD como proxy autonômico
- Chevallier et al. (2024) — MOABB benchmark

---

## Licença

MIT. Dados de participantes não são distribuídos neste repositório (LGPD).
