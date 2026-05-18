# NEUROCALIB

[![CI](https://github.com/Frausino/bci-calib/actions/workflows/ci.yml/badge.svg)](https://github.com/Frausino/bci-calib/actions)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![SBOM: CycloneDX](https://img.shields.io/badge/SBOM-CycloneDX-informational)](https://cyclonedx.org)

Framework de calibração probabilística adaptativa para sistemas multimodais de Interface Cérebro-Computador (Brain-Computer Interface — BCI) utilizando EEG e modulação do estado autonômico via HRV (Heart Rate Variability).

Este projeto investiga se dinâmicas do sistema nervoso autônomo podem melhorar a calibração de confiança em classificadores de imaginação motora através de temperature scaling dinâmico modulado por sinais fisiológicos derivados da variabilidade da frequência cardíaca.

O repositório foi projetado como uma plataforma de engenharia de pesquisa reproduzível integrando:

* calibração probabilística
* processamento de sinais EEG
* modulação fisiológica via HRV
* rastreamento de experimentos
* DevSecOps
* Clean Architecture
* pipelines determinísticos de Machine Learning

PIC IAR/CEUB 2026–2027.

---

# Hipótese de Pesquisa

Métodos tradicionais de calibração assumem distribuições estáticas de confiança durante a inferência.

Este projeto investiga se a qualidade da calibração pode ser melhorada através da adaptação dinâmica do temperature scaling de acordo com o estado do sistema nervoso autônomo estimado por sinais de HRV.

Formulação central:

```math
\tau(r_t) = 1 + (\tau_{max} - 1)\sigma(a r_t)
```

onde:

* (r_t) = estado autonômico normalizado derivado do RMSSD
* (\sigma) = função sigmoide
* (\tau) = temperatura dinâmica de calibração

Estado fisiológico normalizado:

```math
r_t = \frac{RMSSD_{smooth,t} - \mu_{train}}{\sigma_{train}}
```

Principais métricas avaliadas:

* Expected Calibration Error (ECE)
* Brier Score
* Calibration Curves
* Negative Log Likelihood (NLL)

---

# Arquitetura do Sistema

O repositório segue os princípios de Clean Architecture para isolar:

* lógica científica de domínio
* orquestração experimental
* adaptadores de infraestrutura
* interfaces de apresentação

```text
src/bci_calib/
├── domain/           # Regras científicas puras e lógica de calibração
├── application/      # Casos de uso e orquestração
├── infrastructure/   # Integrações e adaptadores externos
└── presentation/     # Interfaces CLI/API
```

## Objetivos Arquiteturais

* reprodutibilidade
* experimentação modular
* isolamento de frameworks
* ambientes determinísticos
* manutenibilidade
* rastreabilidade científica

---

# Estrutura do Repositório

```text
bci-calib/
├── .github/              # Workflows CI/CD
├── docs/                 # Governança e documentação arquitetural
│   └── adr/              # Architecture Decision Records
├── logbook/              # Rastreamento experimental
├── model-cards/          # Documentação de governança de modelos
├── notebooks/            # Apenas exploração e análise
├── results/              # Resultados experimentais
├── src/                  # Código principal
├── tests/                # Testes automatizados
├── DAY_PROTOCOL.md       # Workflow operacional diário
├── SECURITY.md           # Política de segurança
├── justfile              # Executor operacional de comandos
├── pyproject.toml
└── uv.lock
```

---

# Stack de Research Engineering

| Camada                    | Tecnologia     |
| ------------------------- | -------------- |
| Gerenciamento de Ambiente | uv             |
| Packaging                 | Hatchling      |
| Linting                   | Ruff           |
| Formatação                | Ruff Format    |
| Segurança de Tipagem      | mypy strict    |
| Testes                    | pytest         |
| Segurança SAST            | bandit         |
| Secret Scanning           | gitleaks       |
| Auditoria de Dependências | pip-audit      |
| SBOM                      | CycloneDX      |
| Rastreamento Experimental | MLflow         |
| CI/CD                     | GitHub Actions |

---

# Setup

## Instalar uv

```bash
pip install uv
```

## Clonar repositório

```bash
git clone https://github.com/Frausino/bci-calib.git
cd bci-calib
```

## Sincronizar ambiente

```bash
uv sync --all-extras
```

## Instalar hooks pre-commit

```bash
uv run pre-commit install
```

---

# Workflow de Desenvolvimento

Documentação operacional:

```text
DAY_PROTOCOL.md
```

Decisões arquiteturais:

```text
docs/adr/
```

Política de segurança:

```text
SECURITY.md
```

---

# Comandos do Justfile

## Sincronizar dependências

```bash
just sync
```

## Executar lint com Ruff

```bash
just lint
```

## Corrigir automaticamente problemas de lint

```bash
just fix
```

## Formatar código

```bash
just format
```

## Executar verificação de tipagem

```bash
just typecheck
```

## Executar testes

```bash
just test
```

## Executar análise de segurança

```bash
just security
```

## Auditar dependências

```bash
just audit
```

## Gerar SBOM

```bash
just sbom
```

## Executar pipeline completa de validação

```bash
just all
```

## Iniciar interface do MLflow

```bash
just mlflow-ui
```

---

# Protocolo de Validação Científica

Toda modificação relacionada à calibração deve avaliar:

| Métrica           | Objetivo                              |
| ----------------- | ------------------------------------- |
| ECE               | Qualidade da calibração de confiança  |
| Brier Score       | Precisão probabilística               |
| Calibration Curve | Visualização de confiabilidade        |
| NLL               | Qualidade da incerteza probabilística |

---

# Rastreamento Experimental

Os experimentos são rastreados utilizando MLflow.

Artefatos monitorados incluem:

* hiperparâmetros
* métricas de calibração
* parâmetros de pré-processamento
* outputs de modelos
* curvas de avaliação
* metadados experimentais

Roadmap futuro inclui:

* dashboards de benchmark
* linhagem experimental
* estudos comparativos de calibração

---

# Governança

## Decisões Arquiteturais

Documentadas em:

```text
docs/adr/
```

## Segurança

Ver:

```text
SECURITY.md
```

## Reprodutibilidade Científica

Padrões operacionais definidos em:

```text
DAY_PROTOCOL.md
```

---

# DevSecOps

| Área                      | Ferramenta     |
| ------------------------- | -------------- |
| Análise Estática          | Ruff           |
| Análise de Segurança      | bandit         |
| Detecção de Secrets       | gitleaks       |
| Auditoria de Dependências | pip-audit      |
| Geração de SBOM           | CycloneDX      |
| Validação CI              | GitHub Actions |

---

# Roadmap

| Fase    | Objetivo                                        | Status       |
| ------- | ----------------------------------------------- | ------------ |
| Fase 1  | Infraestrutura e governança                     | Em andamento |
| Fase 2A | Pipeline sintético de benchmark                 | Planejado    |
| Fase 2B | Coleta fisiológica experimental                 | Planejado    |
| Fase 3  | Manuscrito científico e validação da plataforma | Planejado    |

---

# Referências

## Calibração

* Guo et al. (2017) — On Calibration of Modern Neural Networks

## BCI e Geometria Riemanniana

* Barachant et al. (2012) — Multiclass Brain-Computer Interface Classification by Riemannian Geometry

## Fisiologia HRV

* Shaffer & Ginsberg (2017) — An Overview of Heart Rate Variability Metrics and Norms

## Benchmarking

* Chevallier et al. (2024) — MOABB: Trustworthy Algorithm Benchmarking for BCIs

---

# Disclaimer

Este repositório é:

* software de pesquisa
* não certificado como software médico
* não destinado a diagnóstico ou tratamento clínico

Nenhum dado fisiológico identificável de participantes é distribuído neste repositório.

Todos os futuros experimentos envolvendo seres humanos devem cumprir:

* LGPD
* aprovação ética institucional
* requisitos de anonimização

---

# Licença

MIT License.
