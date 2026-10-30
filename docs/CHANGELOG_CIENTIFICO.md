# Changelog Científico: bci-calib

Registra mudanças metodológicas que afetam a interpretação dos resultados. Commits técnicos ficam no Git log. Formato: Guia Mestre v5, Seção 0.8.

---

## 2026-10-11: Desenho inferencial (H1 única confirmatória)

**Tipo:** [ ] Metodológico  [ ] Técnico  [ ] Protocolo  [x] Estatístico
**Impacto:** [ ] Pequeno  [ ] Médio  [x] Grande

### Mudança
- Substituição metodológica, antes do pré-registro, da regra de controle familiar α = 0,025 (H1 e H2) do Guia Mestre 0.6.
- H1 é a única hipótese confirmatória: Wilcoxon pareado unilateral, α = 0,05. H2 e H2b são secundárias.
- Contrastes secundários com as condições F e G formam uma família separada, com correção de Holm.
- Amostra-alvo: n = 20 sujeitos analisáveis, poder aproximado de 0,81 para o teste de Wilcoxon de H1 sob d = 0,60 (t não central com a eficiência assintótica relativa do Wilcoxon, 3/π). Para n = 15, o mesmo componente tem poder aproximado de 0,69. O poder da regra composta de corroboração, com os critérios adicionais de relevância e segurança, não foi estimado.
- Degeneração do componente dinâmico: |a| < 0,1.
- Ajuste por NLL, com a ∈ [−10, 0] e τ_max ∈ [1, 5].

### Motivação
Com α = 0,025, n = 19 teria poder de 0,67. Uma única hipótese confirmatória direcional, definida antes dos dados, é coerente com H1 como pergunta central. Detalhes e alternativas em `docs/adr/ADR-007-inferential-design.md`.

### Impacto nos resultados
Ainda não há dados reais. A decisão antecede qualquer coleta e o OSF.

### Arquivos afetados
- docs/adr/ADR-007-inferential-design.md
- docs/power_analysis.py
- src/bci_calib/application/power_analysis.py
- src/bci_calib/application/trial_rmssd_alignment.py
- src/bci_calib/application/session_audit.py
- src/bci_calib/infrastructure/tracking/session_log.py
- DMP.md (minuta)
- docs/TCLE.md
- OSF_PREREG.md

### OSF atualizado: pendente (pré-registro ainda não submetido)
### Validado por: pytest tests/unit/application, mypy --strict, ruff, bandit

---

## 2026-10-11: τ(r_t) com dois parâmetros livres e ablação alinhada ao PIC

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

## 2026-05-25: Entradas iniciais (S3)

| Decisão | Motivação |
|---|---|
| `floor()`, nunca `round()`, no alinhamento k_t = floor(T_t / Δt) | Garantia de causalidade. `round()` traria informação futura para o trial t. |
| α_EMA = 0.3 e Δt = 6.07 s, com τ_EMA ≈ 17 s | Compatível com a dinâmica parassimpática de 15 a 30 s. |
| Família H1 + H2 com α = 0.025 cada | Co-primárias, com α nominal de 0.05 / 2 (Holm). |
| OAS como estimador de covariância | O SCM fica singular quando n_channels / n_trials > 0.1, e o TangentSpace retorna NaN em silêncio. |
| ICA aplicada no Raw, nunca em Epochs | Os índices de canais divergem entre Raw e Epochs. |
| τ_min = 1 e b = 0 fixos | Identificabilidade com n = 19. Implementado em 2026-10-11 (ver acima). |
