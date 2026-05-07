# Sprint 01 — S1 — Repositório, DevSecOps e Identidade

**Período real de execução:** 2026-05-07 a 2026-05-14
**Período oficial do guia:** 2026-08-03 a 2026-08-07
**Fase:** 1 — Infraestrutura e Submissão Ética
**Prioridade:** CORE | 30h

---

## Objetivo

Repositório com CI verde, pre-commit instalado e estrutura
Clean Architecture vazia.

---

## Outputs planejados

- [x] bci-calib/ GitHub público com branch protection em main
- [x] pyproject.toml + uv sync --all-extras sem conflitos
- [x] CI verde em 3.11 e 3.12 (matrix)
- [x] pre-commit: ruff, mypy, bandit, gitleaks, pip-audit
- [x] SBOM CycloneDX integrado ao CI
- [x] src/domain, application, infrastructure, presentation — vazios
- [ ] Tag v0.1.0 publicada

---

## Blockers encontrados

| Blocker                                 | Causa                                     | Resolução                                    |
| --------------------------------------- | ----------------------------------------- | -------------------------------------------- |
| Branch protection requer Pro (privado)  | GitHub Free não suporta em repo privado   | Repositório tornado público                  |
| `uv` não reconhecido no PowerShell      | PATH não atualizado após instalação       | `$env:Path` atualizado + PATH permanente     |
| README.md encoding erro no hatchling    | Arquivo salvo em UTF-16                   | Re-salvo como UTF-8 sem BOM                  |
| `types-all` quebrado no pre-commit mypy | `types-pkg-resources` removido do PyPI    | Substituído por `pydantic>=2.0` apenas       |
| gitleaks v8.19.0 flag bug               | Incompatibilidade com pre-commit          | Downgrade para v8.18.4                       |
| `ModuleNotFoundError: bci_calib` no CI  | `src/` não commitado + falta `pythonpath` | Estrutura commitada + `pythonpath = ["src"]` |
| Python 3.13 detectado pelo uv           | Sistema tem 3.13, projeto requer 3.11     | `uv python pin 3.11`                         |

---

## Decisões registradas

- Início antecipado de S1 em 07/05/2026 (cronograma oficial: ago/2026).
  Ganho de buffer de ~3 meses antes da fase experimental.
- Repositório público desde o início — alinhado com open science e OSF.
- cyclonedx-bom 7.3.0 instalado (mais recente que o >=4.4 especificado).

---

## Resultado

_Preencher ao completar a tag v0.1.0._

---

## Próximo sprint

S2 — Logging, AuditDB SQLite e Correlation IDs (10–14/ago/2026 oficial).
