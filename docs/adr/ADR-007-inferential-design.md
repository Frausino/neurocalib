# ADR-007: Desenho inferencial pré-registrado (H1 única confirmatória)

## Status

Accepted. Resolve as pendências do ADR-006. Entra em vigor com a submissão do pré-registro no OSF.

## Data

2026-10-11

## Contexto

O PIC e o Guia Mestre v5 divergiam em cinco pontos que afetam a análise principal. Todos precisavam de uma decisão antes do pré-registro:

1. **Sinal de `a`.** O PIC usa `a ∈ [−10, 0]`. O Guia S15 usava `a ∈ [0.01, 10]`. A premissa do PIC (RMSSD baixo, τ alto) exige `a ≤ 0`, pois `∂τ/∂r_t = (τ_max − 1)·a·σ·(1 − σ)`.
2. **Objetivo do ajuste.** O PIC usava argmin ECE_val. A Lista de Leitura (C01) e o Guia S15 usavam NLL.
3. **Limites de `τ_max`.** O PIC usava [1, 5]. O Guia S15 usava [1.05, 10]. Com piso de 1,05, o alarme RF-6 (`τ_max` degenerado) nunca dispararia.
4. **Condições F e G.** O Guia incluía Platt e Isotonic. O PIC listava só A a E.
5. **Controle de erro tipo I.** O Guia 0.6 definia H1 e H2 como família com α = 0,025 cada. O PIC testava H1 com p < 0,05 e declarava H1, H2 e H2b como três inferências independentes.

A análise de poder (`docs/power_analysis.py`) mostrou que a família com α = 0,025 reduz o poder de n = 19 de 0,79 para 0,67 (d = 0,60).

## Decisão

| # | Decisão | Valor |
|---|---|---|
| D1 | Sinal de `a` | `a ∈ [−10, 0]`. `a = 0` é permitido e equivale à condição B |
| D2 | Objetivo do ajuste | `argmin NLL` no conjunto de calibração interno (K_inner = 4). ECE, Brier e NLL só fora da amostra |
| D3 | Limites de `τ_max` | `[1, 5]` na análise principal. Sensibilidade `[1, 10]` se `τ̂_max = 5` em mais de 10% dos ajustes |
| D4 | F e G | Benchmarks secundários pré-especificados. Holm-Bonferroni só dentro de {C vs F, C vs G} |
| D5 | Inferência | H1 é a única hipótese confirmatória: Wilcoxon pareado unilateral, α = 0,05. H2 e H2b são secundárias |
| A1 | Degeneração do efeito dinâmico | `|a| < 0,1` (valor do PIC) |
| A2 | Amostra | n = 20 sujeitos analisáveis. Poder aproximado de 0,81 para o teste de Wilcoxon de H1 sob d = 0,60. Cerca de 31 candidatos |
| A3 | Registro | A regra α = 0,025 em família foi substituída antes do pré-registro. É uma substituição metodológica, registrada no CHANGELOG |
| A4 | Contingência CEP | n = 15 tem poder aproximado de 0,69 para o mesmo teste |

### Hierarquia de contrastes

1. Primário: C vs A.
2. Complementar: C vs B.
3. Secundários, com Holm: C vs F e C vs G.
4. Diagnósticos, sem teste confirmatório: C vs D e C vs E.

### Critério de corroboração de H1

Todas as condições precisam valer, com ΔECE = ECE_A − ECE_C e a unidade de análise sendo o sujeito:

1. p unilateral < 0,05 (Wilcoxon pareado, `alternative="greater"`).
2. Mediana de ΔECE ≥ 0,02.
3. Limite inferior unilateral de 95% do bootstrap pareado (B = 2.000) de ΔECE > 0.
4. ΔBrier > 0 e ΔNLL > 0, como corroboração direcional e não como testes adicionais.
5. ΔAUROC ≥ −0,02 (critério de não aceitação do Guia 0.6).

### Poder (aproximação t não central com ARE do Wilcoxon = 3/π)

| Cenário | n | Poder analítico | Monte Carlo (exato, 20.000 simulações) |
|---|---|---|---|
| d = 0,60, α = 0,05 unilateral | 15 | 0,694 | 0,684 |
| | 19 | 0,790 | 0,784 |
| | 20 | 0,810 | 0,810 |
| | 21 | 0,828 | 0,820 |
| d = 0,60, α = 0,025 unilateral | 19 | 0,674 | |
| d = 0,50, α = 0,05 unilateral | 19 | 0,655 | 0,647 |
| | 20 | 0,676 | 0,674 |

Menor n com poder ≥ 0,80: 20 (α = 0,05) e 25 (α = 0,025).

**Alcance dos números.** Para n = 20, o componente inferencial primário de H1, o teste de Wilcoxon pareado unilateral, tem poder aproximado de 0,81 sob d = 0,60. O poder da regra composta de corroboração, que inclui os critérios adicionais de relevância prática e de segurança (Seção 1), não foi estimado e é menor ou igual ao do componente primário.

## Alternativas rejeitadas

- **α = 0,025 em família (H1 e H2).** Poder de 0,67 com n = 19. H2 é um proxy correlacional (RMSSD para log-loss) e não deve consumir o orçamento de erro da pergunta central.
- **ECE como objetivo do ajuste.** Ajustar e testar pela mesma métrica a usaria duas vezes. NLL é regra de pontuação estritamente própria (Gneiting e Raftery, 2007) e é o objetivo de Guo et al. (2017).
- **Piso de 1,05 para `τ_max`.** Elimina a ausência legítima de calibração (`τ_max = 1`) e desativa o alarme RF-6.
- **Limiar `|a| < 0,01`.** Mais permissivo com efeitos dinâmicos mínimos. Mantido o 0,1 do PIC, que é o texto já submetido ao CEUB.

## Consequências

- `docs/power_analysis.py` e `application/power_analysis.py` passam a ser a fonte dos números de poder citados no OSF e no PIC.
- **Invariante de auditoria: cada `run_id` representa exatamente uma sessão.** As métricas são indexadas por `(run_id, key, step)` e não têm coluna de sessão. O vínculo é um artefato `session_log` na mesma run, apontando para o `session_log.json` que contém o `session_id`. O schema atual não tem tags ou metadados por run.
- `application/session_audit.py` e `infrastructure/tracking/session_log.py` gravam `var_r_t` e as três flags no AuditDB (como métricas) e no `session_log.json`. `dynamic_effect_degenerate` e `tau_max_degenerate` ficam nulos até existir um ajuste. O evento nomeado `low_functional_identifiability` exige uma tabela de eventos, que o schema atual não tem.
- `application/trial_rmssd_alignment.py` implementa `k_t = floor(T_t / Δt)` e `Var(r_t) ≥ 0,05`. Os valores de Δt e do lag de segurança são argumentos obrigatórios, para não duplicar constantes congeladas.
- A camada `application` passa a depender de numpy e scipy. A camada `domain` continua sem dependências externas.
- O Guia Mestre (0.6, 0.7 RF-6, S11, S15, S35, Parte 2) e o PIC (seções 2, 4, 6c, 6e, 6g, 8) precisam ser alinhados a esta decisão. A lista está em `OSF_PREREG.md`.
- O fitter da S15 implementa D1 a D3: L-BFGS-B, 5 reinícios, seed = 42, com registro de convergência, ponto inicial, iterações e a flag `at_boundary`.
- A S35 implementa o teste de H1 e o bootstrap pareado conforme o critério acima.

## Backlog técnico

- Gravação transacional em lote das métricas de `record_session_audit` (todas ou nenhuma). Hoje são chamadas separadas e uma falha intermediária pode deixar registro parcial. O vínculo com o `session_log` é gravado primeiro, para que nunca existam métricas sem sessão rastreável.
- Tabela de eventos no AuditDB (evento `low_functional_identifiability`).

## Pendências

Ver a seção "Antes de submeter" do `OSF_PREREG.md`.
