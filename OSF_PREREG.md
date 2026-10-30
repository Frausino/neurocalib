# Pré-registro OSF: bci-calib

Calibração probabilística de classificadores de imagética motora (MI-BCI) dependente do estado autonômico. EEG (OpenBCI Cyton) e HRV (RMSSD, Polar H10).

- Repositório: https://github.com/Frausino/neurocalib
- Versão do código no momento do depósito: `[COMMIT EXATO OU TAG DA S4, preencher no depósito]`. A tag `v0.3.0` é anterior ao código da S4 e não serve como referência
- Autor: Davi Rosa F. (PIC IAR/CEUB 2026-2027)
- Tipo de depósito no OSF: **Pre-registration** (nunca Draft)
- Data de submissão: `[PREENCHER NA SUBMISSÃO]`
- URL do registro: `[PREENCHER APÓS A SUBMISSÃO]`
- Fontes de decisão: `docs/adr/ADR-006`, `docs/adr/ADR-007`, `docs/CHANGELOG_CIENTIFICO.md`

## Antes de submeter

Este arquivo só vira o pré-registro depois que os itens abaixo forem resolvidos e removidos. O texto do OSF não pode conter lacunas.

| # | Pendência | Origem |
|---|---|---|
| B1 | Cenários A, B e C da análise adaptativa de H2 (piloto). O PIC os cita como "pré-registrados no OSF", mas a definição não consta no PIC, no Guia nem na Lista de Leitura. Definir os três cenários e a regra de decisão antes do depósito | PIC 7 e 8 |
| B2 | Definição de "sujeito analisável" (G24). O Guia exige que ela conste no OSF e não a define. A Seção 3.3 abaixo é uma proposta montada só com critérios do PIC. Confirmar | Guia S4 |
| B3 | O PIC cita "K_outer = 5" em 6c e "LOSO sobre k = 4 sessões" em 6f. Com 4 sessões por sujeito, K_outer = 5 não se aplica. Esta minuta usa LOSO. Confirmar e corrigir o PIC | PIC 6c e 6f |
| B4 | O PIC (Seção 8) chama H2 de "confirmatório (LME AR(1))". Pela decisão D5, H2 é secundária. Corrigir o PIC | PIC 8 |
| B5 | Número de inscritos. A meta passou a 20 analisáveis e a ≈ 31 candidatos. O PIC fixa 19 inscritos e a carga de coleta (19 × 4 × 25 min ≈ 31,7 h). Definir quantos inscritos são necessários e recalcular a carga | A2 |
| B6 | Variância de r_t: esta minuta usa variância amostral (ddof = 1) e lag de segurança de 2 s antes do onset. Confirmar | PIC 6e |
| B7 | Alinhar o Guia Mestre e o PIC conforme a Seção 9 | ADR-007 |
| B8 | Campos institucionais do TCLE e do DMP (instituição, CEP, contatos, prazo de eliminação na retirada, política de compartilhamento de dados). Ver `docs/TCLE.md` e `DMP.md`. Inclui o procedimento para achados incidentais e a base normativa (CNS 466/2012 como principal; 510/2016 a confirmar com o CEP) | S4 |

## 1. Perguntas e hipóteses

**Pergunta central.** Em que medida a calibração por temperatura dinâmica τ(r_t), modulada pelo RMSSD derivado de ECG, reduz o ECE de classificadores EEG de imagética motora em relação ao classificador sem calibração?

**H1 (única hipótese confirmatória).** Com ΔECE = ECE_A − ECE_C, calculado por sujeito fora da amostra, a condição C (τ dinâmico) reduz o ECE em relação à condição A (EEG puro).

- Teste: Wilcoxon pareado unilateral (`alternative = "greater"` sobre ΔECE), α = 0,05, unidade de análise = sujeito.
- Tamanho de efeito: r = Z/√n.
- Intervalo: bootstrap pareado sobre sujeitos, B = 2.000, limite inferior unilateral de 95%.
- **H1 é corroborada se todas as condições valerem:**
  1. p unilateral < 0,05.
  2. Mediana de ΔECE ≥ 0,02.
  3. Limite inferior unilateral de 95% do bootstrap de ΔECE > 0.
  4. ΔBrier > 0 e ΔNLL > 0 (corroboração direcional, sem testes adicionais).
  5. ΔAUROC ≥ −0,02. Melhora de ECE com perda de discriminação não é aceita.
- Âncora de efeito esperado: ΔECE ≥ 0,05 (ECE_A de referência ≈ 0,12, faixa típica 0,10 a 0,15; Guo et al., 2017; Minderer et al., 2021).

**H2 (secundária, piloto n = 1 a 3, exploratória).** Associação monotônica negativa entre r_t e a perda logarítmica l_t. Spearman com permutação em blocos (b = 8, B = 1.000, α = 0,05). A correlação cruzada defasada ρ_lag(r_t, l_{t+k}), k ∈ {−2, −1, 0, +1, +2} tentativas, é inspecionada graficamente: associação genuína tem pico em k = 0. Modelo linear misto com intercepto aleatório e AR(1) como análise complementar.

**H2b (secundária).** ρ entre sessões < 0 e |ΔECE_watch| < 0,05 (relógio versus Polar H10).

H2 e H2b não são usadas para declarar a eficácia do método. Seus resultados são reportados como secundários.

## 2. Modelo

    P(y | X) = softmax(z / τ(r_t))
    τ(r_t)   = 1 + (τ_max − 1) · σ(a · r_t)
    r_t      = (RMSSD_smooth_t − μ_train) / σ_train

- `τ_min = 1` e `b = 0` são fixos. Os parâmetros livres são θ = (τ_max, a).
- Para a ≤ 0, RMSSD baixo implica τ alto: o classificador reduz a confiança sob carga autonômica elevada.
- a = 0 colapsa o modelo para temperature scaling estático (condição B).
- μ_train e σ_train vêm só dos dados de treino. r_t usa o lag de segurança de 2 s antes do onset da imagética.

## 3. Amostra e protocolo

### 3.1 Amostra

- Voluntários adultos saudáveis, 18 a 40 anos, destros, sem doença neurológica ou cardiovascular por autorreferência.
- **Meta: n = 20 sujeitos analisáveis**, com poder aproximado de 0,81 para o teste de Wilcoxon de H1 sob d = 0,60 (Seção 7). Recrutamento de ≈ 31 candidatos, pela razão candidatos para analisáveis do PIC (15 / 23,5 ≈ 0,64).
- Contingência CEP: n = 15 analisáveis, poder aproximado de 0,69 para o mesmo teste.
- Sujeitos com acurácia de MI < 60% permanecem na amostra e são analisados também como subgrupo de BCI illiteracy (Blankertz et al., 2010; Jeunet et al., 2015).
- Piloto n = 1 a 3: validação técnica do pipeline e teste exploratório de H2. A coleta principal ocorre independentemente do resultado do piloto.

### 3.2 Sessões

- 4 sessões por sujeito, intervalo de 48 a 72 h, sequência ABBA (A manhã, B tarde).
- 80 tentativas por sessão (40 esquerda, 40 direita), no mínimo 320 por sujeito.
- Cada sessão: repouso de 5 min com Polar H10 e relógio via LSL, depois 80 tentativas com EEG e ECG simultâneos.
- Sessões com mais de 20% de tentativas excluídas por jitter > 40 ms são repetidas em até 72 h.

### 3.3 Sujeito analisável (G24, proposta a confirmar em B2)

Um sujeito é analisável quando:

1. completou as 4 sessões;
2. nenhuma sessão ficou com mais de 20% de tentativas excluídas por jitter > 40 ms após a repetição permitida;
3. não houve impedância persistente > 15 kΩ após dois reposicionamentos;
4. não há contraindicação neurológica confirmada.

Acurácia de MI < 60% **não** exclui o sujeito.

### 3.4 Exclusões de sessão

Sessões com Var(r_t) < 0,05 não são excluídas. Elas formam um subgrupo analisado à parte (Seção 6).

## 4. Aquisição e pré-processamento

- EEG: OpenBCI Cyton, 250 Hz, 8 canais totais, incluindo C3, C4, Cz, CP3, CP4 e Fz. Fz serve só à rejeição de artefatos oculomotores.
- Filtro passa-banda 0,5 a 40 Hz (Butterworth, ordem 4), notch em 60 Hz.
- ICA aplicada no Raw, nunca em Epochs. Rejeição automática por ICLabel com probabilidade ≥ 0,80 (categorias "eye" e "muscle"). Auditoria de 10% por avaliador cego. Número de componentes rejeitados reportado como variável de controle.
- Épocas de [−0,5; 4,5] s ao redor do onset. Rejeição por pico a pico > 80 µV em qualquer canal.
- Covariâncias riemannianas com estimador OAS, nunca SCM.
- ECG: Polar H10, 1 kHz. QC de HRV: descartar janelas com menos de 3 picos R e intervalos RR < 300 ms ou > 2000 ms.
- Sincronização EEG-ECG por LSL, latência ≤ 10 ms.

## 5. Alinhamento causal do RMSSD e suavização

- RMSSD calculado em janela deslizante de 30 s de intervalos RR, atualizado a cada Δt = 6,07 s.
- Suavização exponencial com α_EMA = 0,3, o que dá τ_EMA = −Δt / ln(1 − α) = −6,07 / ln(0,70) ≈ 17 s.
- Sensibilidade de α_EMA ∈ {0,1; 0,2; 0,3; 0,5} no piloto, por Spearman maximizado em valor absoluto. Em caso de empate, α_EMA = 0,3. A seleção usa só dados de calibração, nunca de teste (G02).
- **Alinhamento: k_t = floor(T_t / Δt)**, com T_t igual ao onset do trial menos o lag de segurança de 2 s. A amostra k da série suavizada é a mais recente que não é posterior a T_t. `round()` é proibido: introduziria informação futura. Implementação e testes: `application/trial_rmssd_alignment.py`, `test_causal_alignment` e `test_no_lookahead`.

## 6. Ajuste, validação e identificabilidade

### 6.1 Ajuste

- Objetivo: `argmin NLL` no conjunto de calibração interno (K_inner = 4).
- L-BFGS-B com 5 reinícios e seed = 42.
- Limites: `τ_max ∈ [1, 5]` e `a ∈ [−10, 0]`. `a = 0` é permitido.
- Registrar por ajuste: convergência, ponto inicial, iterações e a flag `at_boundary`.
- Sensibilidade com `τ_max ∈ [1, 10]` apenas se τ̂_max = 5 em mais de 10% dos ajustes.
- ECE, Brier e NLL são calculados **somente fora da amostra**.

### 6.2 Validação

- LOSO externo, por sujeito. Resultados por fold reportados individualmente além da média.
- Unidade de análise: sujeito. Janelas e tentativas não são unidades independentes.

### 6.3 Identificabilidade e degeneração

- **Var(r_t) < 0,05** em uma sessão marca `functionally_identifiable = False`. A sessão é mantida e analisada como subgrupo, onde C deve igualar B. Variância amostral (B6).
- **Efeito dinâmico degenerado:** |â| < 0,1 (`dynamic_effect_degenerate`).
- **τ_max degenerado:** τ̂_max ≤ 1,05 (`tau_max_degenerate`).
- As três flags (`functional_identifiable`, `dynamic_effect_degenerate`, `tau_max_degenerate`) entram no `session_log.json` e no AuditDB como métricas (`var_r_t`, `functional_identifiable`, `dynamic_effect_degenerate`, `tau_max_degenerate`). Implementação: `application/session_audit.py` e `infrastructure/tracking/session_log.py`. As duas últimas só existem depois do ajuste (S15). O evento nomeado `low_functional_identifiability` depende de uma tabela de eventos que o schema atual do AuditDB não tem, e fica para a evolução do schema por ADR.
- Critério de robustez: resultado consistente em pelo menos 3 de 5 condições de agregação.

## 7. Poder

Aproximação t não central para o teste t pareado, com n substituído por n × ARE, ARE = 3/π ≈ 0,9549 (Wilcoxon sob normalidade). Verificação por Monte Carlo com o teste de Wilcoxon exato (20.000 simulações, seed = 42). Código: `docs/power_analysis.py`.

Para n = 20, o componente inferencial primário de H1, o teste de Wilcoxon pareado unilateral, tem poder aproximado de 0,81 sob d = 0,60. O poder da regra composta de corroboração, que inclui os critérios adicionais de relevância prática e de segurança (Seção 1), não foi estimado e é menor ou igual ao do componente primário.


| Cenário | n | Analítico | Monte Carlo |
|---|---|---|---|
| d = 0,60, α = 0,05 unilateral | 15 | 0,694 | 0,684 |
| | 19 | 0,790 | 0,784 |
| | **20** | **0,810** | **0,810** |
| | 21 | 0,828 | 0,820 |
| d = 0,60, α = 0,025 unilateral (regra substituída) | 19 | 0,674 | |
| d = 0,50, α = 0,05 unilateral (limitação declarada) | 19 | 0,655 | 0,647 |
| | 20 | 0,676 | 0,674 |

Menor n com poder ≥ 0,80 para d = 0,60: 20 (α = 0,05) e 25 (α = 0,025).

## 8. Ablação e hierarquia de contrastes

| Condição | Descrição |
|---|---|
| A | EEG puro, τ = 1, sem calibração |
| B | Temperature scaling estático global |
| C | τ(r_t) dinâmico modulado por RMSSD (modelo proposto) |
| D | Incerteza epistêmica interna (MC Dropout ou Bootstrap) |
| E | RMSSD como feature discriminante, sem modulação de τ |
| F | Platt scaling |
| G | Isotonic regression |

1. **Primário:** C vs A (H1).
2. **Complementar:** C vs B (isola a contribuição dinâmica de r_t).
3. **Secundários:** C vs F e C vs G. Holm-Bonferroni somente dentro da família {C vs F, C vs G}.
4. **Diagnósticos, sem teste confirmatório:** C vs D e C vs E.

Métricas: ECE, Brier, NLL, AUROC (MCE e kappa descritivos). ECE com B = 10 bins uniformes em [0,1], com sensibilidade por binning adaptativo (equal-frequency).

## 9. Mudanças em relação aos documentos anteriores

Registradas em `docs/CHANGELOG_CIENTIFICO.md` e `docs/adr/ADR-007-inferential-design.md`.

| Tema | Antes | Agora |
|---|---|---|
| Família de hipóteses | H1 e H2 com α = 0,025 cada (Guia 0.6) | H1 única confirmatória, unilateral, α = 0,05 |
| H2 e H2b | Inferências independentes (PIC 6e) | Secundárias |
| Parâmetros | θ = (τ_min, τ_max, a, b) (PIC) | θ = (τ_max, a) |
| Objetivo do ajuste | argmin ECE_val (PIC) | argmin NLL |
| Limites | `a ∈ [0,01; 10]`, `τ_max ∈ [1,05; 10]` (Guia S15) | `a ∈ [−10, 0]`, `τ_max ∈ [1, 5]` |
| RF-6 | τ_max < 1,05 | τ̂_max ≤ 1,05 |
| Amostra | n = 19, poder 0,80 (PIC) | n = 20 analisáveis, poder ≈ 0,81 (componente Wilcoxon de H1) |
| Contingência CEP | n = 15, poder 0,70 | n = 15, poder ≈ 0,69 (componente Wilcoxon de H1) |
| Sensibilidade d = 0,50 | poder 0,70 (PIC) | poder ≈ 0,68 com n = 20 |
| Ablação | A a E (PIC) | A a G, com F e G secundárias |

Seções a corrigir no Guia: 0.6 (α, bounds), 0.7 RF-6, S11, S15 passo 1, S35 passos 2 e 3, Parte 2 (Equações). Seções a corrigir no PIC: 2 (H1), 5 §4 (Revisão), 6c, 6e, 6g, 7 e 8.

## 10. Análises exploratórias (fora do pré-registro confirmatório)

Subgrupos (illiteracy, Var(r_t) baixa), sensibilidade de α_EMA, sensibilidade de τ_max até 10, tipologia de non-responders, ablação com D e E, concordância smartwatch-ECG (Bland-Altman, regressão de Deming), modelo misto. Tudo que não está nas Seções 1 a 8 é exploratório e rotulado como tal.

## 11. Confundidores declarados

Arousal, temperatura, ciclo circadiano e variabilidade basal do RMSSD, mitigados por z-score intrassujeito e pelo delineamento ABBA (Shaffer et al., 2017). Limitação estrutural: H2 (RMSSD para log-loss) é um proxy correlacional. A cadeia cortical RMSSD para ERD não é testada diretamente.
