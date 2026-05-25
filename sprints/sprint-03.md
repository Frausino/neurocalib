# Sprint 03 — S3 Domain Layer

## Período

2026-05-25

## Objetivo

Implementar a camada de domínio pura da S3, contendo equação de calibração `τ(r_t)`, entidades, objetos de valor e ports/protocols sem dependências externas indevidas.

## Escopo

### Calibration

- `CalibrationParams`
- `_stable_sigmoid`
- `compute_tau`

### Entities e Value Objects

- `AblationCondition`
- `Epoch`
- `RRInterval`
- `Participant`
- `SessionMetadata`

### Ports

- `EEGSource`
- `HRVSource`
- `MIClassifier`
- `Calibrator`

## Critérios de aceite

- [x] `domain/` sem `numpy`, `torch`, `mne`, `scipy` ou `sklearn`
- [x] `CalibrationParams` frozen
- [x] `compute_tau(0.0, CalibrationParams(3.0, 1.0)) == 2.0`
- [x] `AblationCondition` com 7 valores A–G
- [x] `SessionMetadata.functionally_identifiable: bool`
- [x] Protocols com `@runtime_checkable`
- [x] Testes unitários em `tests/unit/domain`
- [x] `mypy --strict` limpo no domínio
- [x] Coverage individual de `domain/`: 100%

## Validação

```powershell
uv run pytest tests/unit/domain -q --override-ini addopts="" --cov=src/bci_calib/domain --cov-report=term-missing --cov-fail-under=100
uv run mypy src/bci_calib/domain --strict
uv run ruff check src/bci_calib/domain tests/unit/domain
uv run bandit -r src/bci_calib/domain

## Resultado

Sprint S3 concluída com status GO para Domain Layer.
