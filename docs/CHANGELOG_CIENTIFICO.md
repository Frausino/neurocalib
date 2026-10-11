# Changelog Científico — bci-calib

Registra mudanças metodológicas que afetam a interpretação dos resultados. Commits técnicos ficam no Git log. Formato: Guia Mestre v5, Seção 0.8.

---

## 2026-10-11 — Atualização do uv.lock (versões da pilha científica)

**Tipo:** [ ] Metodológico  [x] Técnico  [ ] Protocolo  [ ] Estatístico
**Impacto:** [x] Pequeno  [ ] Médio  [ ] Grande

### Mudança
`uv lock --upgrade` para zerar as vulnerabilidades conhecidas (pip-audit: 147 em 17 pacotes, antes). Versões científicas resultantes: mne 1.13.2, moabb 1.7.2, pyriemann 0.12, braindecode 1.8.1, torch 2.14.1, scikit-learn 1.9.1, mlflow 3.17.0.

### Motivação
O hook pip-audit antigo auditava o ambiente isolado do próprio hook, não o projeto. Com o hook corrigido, o lock antigo reprovava o CI.

### Impacto nos resultados
Nenhum resultado foi gerado ainda. O PIC (Seção 6d) cita MNE-Python 1.12, pyriemann 0.9 e braindecode 1.3.2; o Método do manuscrito deve citar as versões do uv.lock usado na análise final.

### Risco residual aceito
PYSEC-2026-3447 (setuptools < 83): neurokit2 0.2.13 exige setuptools<82. Ignorado no pip-audit até o neurokit2 liberar.

### Arquivos afetados
- uv.lock
- .pre-commit-config.yaml

### OSF atualizado: N/A
### Validado por: 140 testes (Python 3.11 e 3.12), mypy --strict, ruff, bandit, pip-audit

---

## 2026-10-11 — τ(r_t) com dois parâmetros livres e ablação alinhada ao PIC

**Tipo:** [x] Metodológico  [x] Técnico  [ ] Protocolo  [ ] Estatístico
**Impacto:** [ ] Pequeno  [x] Médio  [ ] Grande

### Mudança
- `CalibrationParams` passa de `(tau_min, tau_max, a, b)` para `(tau_max, a)`. `TAU_MIN = 1.0` e `SIGMOID_BIAS = 0.0` viram constantes.
- `AblationCondition` C, D e E passam a ter os significados do PIC: C é τ(r_t), D é a incerteza epistêmica e E é RMSSD como feature.
- Os marcadores de conflito de merge foram removidos do docstring de `CalibrationParams`.

### Motivação
O código divergia do PIC e das Decisões Imutáveis (Seção 0.6). O contraste C vs. A apontaria para a condição errada.

### Impacto nos resultados
Ainda não há dados reais. Com isso, o modelo implementado volta a ser idêntico ao modelo a pré-registrar.

### Arquivos afetados
- src/bci_calib/domain/calibration.py
- src/bci_calib/domain/value_objects.py
- src/bci_calib/domain/ports.py (docstrings)
- src/bci_calib/domain/entities.py (docstring)
- tests/unit/domain/*
- docs/adr/ADR-006-tau-two-parameter-and-ablation-semantics.md

### OSF atualizado: N/A (pré-registro ainda não submetido)
### Validado por: pytest tests/unit/domain (100% de cobertura), mypy --strict, ruff, bandit

---

## 2026-05-25 — Entradas iniciais (S3)

| Decisão | Motivação |
|---|---|
| `floor()`, nunca `round()`, no alinhamento k_t = floor(T_t / Δt) | Garantia de causalidade. `round()` traria informação futura para o trial t. |
| α_EMA = 0.3 e Δt = 6.07 s, com τ_EMA ≈ 17 s | Compatível com a dinâmica parassimpática de 15 a 30 s. |
| Família H1 + H2 com α = 0.025 cada | Co-primárias, com α nominal de 0.05 / 2 (Holm). |
| OAS como estimador de covariância | O SCM fica singular quando n_channels / n_trials > 0.1, e o TangentSpace retorna NaN em silêncio. |
| ICA aplicada no Raw, nunca em Epochs | Os índices de canais divergem entre Raw e Epochs. |
| τ_min = 1 e b = 0 fixos | Identificabilidade com n = 19. Implementado em 2026-10-11 (ver acima). |
