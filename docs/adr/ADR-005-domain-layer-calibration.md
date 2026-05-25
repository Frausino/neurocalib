# ADR-005 — Domain Layer: calibração τ(r_t), entidades e ports

## Status

Accepted

## Data

2026-05-25

## Contexto

A S3 implementa a camada de domínio do projeto `bci-calib`, responsável por representar regras matemáticas, entidades, objetos de valor e contratos abstratos relacionados à calibração probabilística dependente do estado autonômico.

O objetivo arquitetural é manter `src/bci_calib/domain/` puro, testável e independente de bibliotecas de infraestrutura, processamento de sinais ou aprendizado de máquina.

A camada de domínio não deve importar:

- `numpy`
- `scipy`
- `mne`
- `torch`
- `sklearn`
- `mlflow`

Essas dependências pertencem às camadas de infraestrutura, aplicação ou experimentação.

## Decisão

A S3 define quatro decisões principais.

### 1. Calibração τ(r_t) no domínio

A função de temperatura dependente do estado autonômico foi modelada como:

    τ(r_t) = τ_min + (τ_max − τ_min) · σ(a · r_t + b)

onde:

- `τ(r_t)` é a temperatura de calibração;
- `r_t` é o índice autonômico no tempo `t`;
- `τ_min` é o limite inferior da temperatura;
- `τ_max` é o limite superior da temperatura;
- `a` controla a inclinação da curva;
- `b` controla o deslocamento;
- `σ` é a função sigmoid logística.

A implementação usa sigmoid numericamente estável para evitar overflow em valores extremos.

Critério funcional validado:

    compute_tau(0.0, CalibrationParams(3.0, 1.0)) == 2.0

### 2. Entidades e objetos de valor imutáveis

Foram definidos modelos imutáveis para representar conceitos centrais do domínio:

- `CalibrationParams`
- `AblationCondition`
- `Epoch`
- `RRInterval`
- `Participant`
- `SessionMetadata`

A imutabilidade reduz efeitos colaterais e facilita testes determinísticos.

### 3. AblationCondition com sete condições

`AblationCondition` foi definido como `str Enum` com sete valores:

    A, B, C, D, E, F, G

As condições `F` e `G` foram reservadas para estratégias de calibração clássicas:

- `F`: Platt scaling
- `G`: Isotonic regression

Essa decisão permite rastrear experimentos de ablação de forma explícita e serializável.

### 4. Ports como protocols runtime-checkable

Foram definidos ports com `typing.Protocol` e `@runtime_checkable`:

- `EEGSource`
- `HRVSource`
- `MIClassifier`
- `Calibrator`

Esses ports definem contratos sem acoplar o domínio a implementações concretas.

O domínio conhece apenas os contratos. A infraestrutura decide como carregar EEG, HRV, modelos e estimadores.

## Decisão sobre `functionally_identifiable`

`SessionMetadata` inclui o campo:

    functionally_identifiable: bool

Esse campo representa se a sessão possui variação autonômica suficiente para sustentar inferência funcional sobre modulação por estado.

Critério conceitual:

    Var(r_t) >= 0.05

A decisão foi manter o campo como booleano, em vez de calcular a variância dentro da entidade, porque:

1. o cálculo estatístico depende da série temporal completa;
2. a entidade deve permanecer leve e serializável;
3. o domínio não deve depender de arrays ou bibliotecas numéricas;
4. a responsabilidade de cálculo pertence à camada de aplicação ou infraestrutura.

## Decisão sobre OAS

OAS, Oracle Approximating Shrinkage, será usado em etapas posteriores como estimador regularizado de covariância para pipelines EEG.

A S3 não implementa OAS no domínio.

Motivo:

- OAS depende de operações matriciais;
- sua implementação prática pertence à infraestrutura ou pipeline experimental;
- importar `sklearn`, `numpy` ou `scipy` em `domain/` violaria a arquitetura limpa.

Portanto, a S3 apenas prepara contratos e entidades para uso futuro de OAS fora do domínio.

## Alternativas consideradas

### Alternativa 1 — Usar arrays diretamente em `Epoch`

Rejeitada.

Motivo: colocaria dados brutos EEG dentro da camada de domínio e forçaria dependência de `numpy`, `mne` ou estruturas similares.

### Alternativa 2 — Calcular `functionally_identifiable` dentro de `SessionMetadata`

Rejeitada.

Motivo: exigiria acesso à série completa de `r_t` e introduziria responsabilidade estatística dentro de uma entidade de metadata.

### Alternativa 3 — Implementar OAS diretamente em `domain/`

Rejeitada.

Motivo: OAS é computacional e matricial, não uma regra de domínio pura. Sua implementação pertence a infraestrutura, aplicação ou experimentação.

### Alternativa 4 — Usar classes abstratas em vez de `Protocol`

Rejeitada.

Motivo: `Protocol` permite tipagem estrutural, reduz acoplamento por herança e facilita mocks/test doubles em testes.

## Consequências positivas

- `domain/` permanece puro e desacoplado.
- Testes unitários são rápidos e determinísticos.
- Contratos de infraestrutura ficam explícitos.
- A arquitetura permite evolução futura para pipelines EEG/HRV sem reescrever entidades.
- `AblationCondition` permite rastreabilidade experimental.
- A separação entre domínio e infraestrutura reduz risco de acoplamento prematuro.

## Consequências negativas

- Algumas validações estatísticas ficam fora das entidades.
- O domínio não executa diretamente operações sobre arrays.
- Implementações concretas exigirão adapters nas camadas superiores.
- A tipagem estrutural com `Protocol` exige testes específicos para garantir conformidade em runtime.

## Validação

A decisão foi validada com:

    mypy src/bci_calib/domain --strict
    pytest tests/unit/domain
    ruff check src/bci_calib/domain tests/unit/domain
    bandit -r src/bci_calib/domain

Critérios confirmados:

    S3 ACCEPTANCE CRITERIA: PASS

Também foram confirmados:

- `compute_tau(0.0, CalibrationParams(3.0, 1.0)) == 2.0`
- `AblationCondition` possui 7 valores A–G
- `SessionMetadata.functionally_identifiable` existe e é booleano
- `domain/` não importa bibliotecas proibidas

## Resultado

A S3 foi aceita como camada de domínio inicial para calibração probabilística dependente do estado autonômico.

Status final:

    S3 — GO
