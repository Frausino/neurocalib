# ADR-006 — τ(r_t) com dois parâmetros livres e semântica da ablação A–G

## Status

Accepted. Substitui parcialmente o ADR-005.

## Data

2026-10-11

## Contexto

A revisão da S3 encontrou três divergências entre o código e o PIC pré-registrado:

1. `CalibrationParams` tinha quatro parâmetros livres (`tau_min`, `tau_max`, `a`, `b`). O PIC e as Decisões Imutáveis do Guia Mestre (Seção 0.6) fixam `τ_min = 1` e `b = 0`. O README já descrevia o modelo de dois parâmetros.
2. O teste GO usava `CalibrationParams(3.0, 1.0)` como `tau_min = 3`, `tau_max = 1`, o que invertia o significado de "mínimo" e "máximo".
3. `AblationCondition` atribuía a C, D e E significados diferentes dos do PIC. O contraste principal C vs. A apontaria para a condição errada.

O docstring de `CalibrationParams` também tinha marcadores de conflito de merge (`<<<<<<<`, `=======`, `>>>>>>>`) com duas versões contraditórias.

## Decisão

### 1. Modelo de calibração

    τ(r_t) = 1 + (τ_max − 1) · σ(a · r_t)

- `TAU_MIN = 1.0` e `SIGMOID_BIAS = 0.0` são constantes do módulo `domain/calibration.py`.
- `CalibrationParams` tem apenas `tau_max` e `a`, nessa ordem posicional.
- `tau_max >= 1.0` é validado na construção, e valores não finitos são rejeitados.
- O sinal de `a` não é restringido no domínio. Os limites de busca pertencem ao fitter, na camada de aplicação.

O GO/NO-GO continua válido e agora tem a semântica correta:

    compute_tau(0.0, CalibrationParams(3.0, 1.0)) == 2.0   # τ_max = 3, a = 1

### 2. Semântica da ablação

| Condição | Significado |
|---|---|
| A | EEG puro, τ = 1, sem calibração |
| B | Temperature scaling estático global |
| C | τ(r_t) dinâmico modulado por RMSSD (modelo proposto) |
| D | Incerteza epistêmica interna (MC Dropout ou Bootstrap) |
| E | RMSSD como feature discriminante, sem modulação de τ |
| F | Platt scaling |
| G | Isotonic regression |

De A a E, segue o PIC. F e G seguem o Guia Mestre. `AblationCondition.description` expõe esse significado para tags do MLflow.

### 3. Sessões não identificáveis

`functionally_identifiable = False` não exclui a sessão. Conforme o pré-registro, a sessão entra num subgrupo analisado separadamente.

## Pendências fora deste ADR

- **Sinal de `a`.** O PIC define `a ∈ [−10, 0]`, porque τ deve subir quando o RMSSD cai. O mission card S15 do Guia define `a ∈ [0.01, 10]`. Decidir antes da S15.
- **Objetivo de ajuste.** O PIC usa argmin ECE_val. A Lista de Leitura (C01) usa NLL com L-BFGS-B. Decidir antes da S15.
- **Limites de `τ_max`.** O PIC usa [1, 5]. O Guia S15 usa [1.05, 10].

## Consequências

- Mudança de API: chamadas `CalibrationParams(tau_min=..., b=...)` deixam de existir.
- Os testes de domínio foram reescritos. A cobertura de `domain/` segue em 100%.
- Volta a ser possível alinhar o código ao OSF sem ambiguidade.
