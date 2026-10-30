# Plano de Gestão de Dados (DMP): bci-calib

Versão: 0.1 (minuta). Última revisão: 2026-10-11. Responsável: Davi Rosa F. Orientador(a): `[PREENCHER]`.

Os itens `[PREENCHER]` e "decisão B8" dependem de definição institucional. Todo o resto vem do PIC, do Guia Mestre ou do repositório.

## 1. Dados do estudo

| Dado | Origem | Sensível (LGPD) | Formato | Onde fica |
|---|---|---|---|---|
| EEG bruto, 8 canais, 250 Hz | OpenBCI Cyton | Sim | BIDS | Armazenamento seguro, fora do Git |
| Intervalos RR e ECG, 1 kHz | Polar H10 | Sim | BIDS | Armazenamento seguro, fora do Git |
| PPG, 25 Hz | Smartwatch | Sim | BIDS | Armazenamento seguro, fora do Git |
| Triagem e metadados (idade, lateralidade) | Questionário online | Sim | `[PREENCHER]` | Armazenamento seguro, fora do Git |
| Tabela código ↔ identidade | Pesquisador | Sim | `[PREENCHER]` | Local separado dos dados (Seção 3) |
| `session_log.json` por sessão | Pipeline | Sim: dado pessoal pseudonimizado, vinculável ao participante enquanto existir possibilidade razoável de ligação | JSON | Pasta da sessão |
| Rastreabilidade (AuditDB, MLflow, logs) | Pipeline | Sim: dado pessoal pseudonimizado, vinculável ao participante enquanto existir possibilidade razoável de ligação | SQLite, MLflow, structlog | Local do projeto, fora do Git |
| Código, ADRs e pré-registro | Repositório | Não | Texto | GitHub |

## 2. Princípios

- **Dados brutos e dados pessoais nunca entram no Git.** O CI inclui gitleaks e o `.gitignore` cobre `audit.db`, `mlflow.db` e artefatos locais.
- **Minimização:** só se coleta o que o PIC prevê.
- **Nenhum identificador direto em logs, nomes de arquivo ou métricas.** Somente o código do sujeito e o `correlation_id` (`exp_{gitHash}_{ts}_{uid4}`). Pseudonimização não é anonimização: esses registros continuam sendo dados pessoais e seguem as mesmas regras de acesso, retenção e eliminação.
- **Unidade de análise = sujeito.** A estrutura de pastas e de registros preserva o vínculo sessão ↔ sujeito por código.

## 3. Pseudonimização

1. Cada voluntário recebe um código (`sub-XX`) na triagem.
2. A tabela código ↔ identidade é guardada separadamente dos dados, com acesso restrito ao pesquisador responsável e ao(à) orientador(a).
3. Arquivos de dados e de sessão usam apenas o código.
4. `[decisão B8: local e proteção da tabela (por exemplo, volume criptografado)]`

## 4. Armazenamento e backup

- Política **3-2-1** (PIC): 3 cópias, 2 mídias diferentes, 1 fora do local principal.
- Cópia 1: `[PREENCHER]`. Cópia 2: `[PREENCHER]`. Cópia externa: `[PREENCHER]`.
- Proteção em repouso e em trânsito: `[decisão B8]`.
- Teste de restauração do backup antes da primeira coleta e depois a cada `[PREENCHER]`.

## 5. Acesso e segurança

- Privilégio mínimo: pesquisador responsável e orientador(a). `[PREENCHER: demais pessoas, se houver]`
- Sem acesso de terceiros a dados identificáveis.
- Incidente de segurança: registrar, conter, avisar orientador(a) e CEP. `[PREENCHER: contato do encarregado da instituição]`

## 6. Retenção e eliminação

- Retenção de **5 anos** após o fim da pesquisa (PIC e TCLE). Depois, eliminação ou anonimização.
- Eliminação registrada em um **registro de eliminação** sem dados pessoais: data, código, tipo de dado, cópias tratadas.

## 7. Retirada de participante

Segue o TCLE (`docs/TCLE.md`, Seção 8). Procedimento técnico:

1. Localizar o código na tabela e confirmar a identidade do pedido.
2. Parar qualquer coleta nova.
3. Eliminar sinais brutos, derivados identificáveis, triagem e a linha da tabela de códigos, **nas 3 cópias de backup**.
4. Marcar o sujeito como retirado, para que não entre em nenhuma análise futura.
5. Registrar a eliminação no registro de eliminação.
6. Enviar ao participante a confirmação por escrito no prazo do TCLE `[decisão B8]`.
7. Se o participante já estiver em análise publicada, resultados agregados e anonimizados são mantidos, e isso consta no TCLE.

## 8. Compartilhamento e publicação

- Código: GitHub, com release e DOI no Zenodo conforme o Guia (S47).
- Pré-registro: OSF.
- Dados individuais (EEG, ECG): `[decisão B8: não compartilhar, compartilhar anonimizados sob solicitação ou publicar em repositório]`. Sinais de EEG e de ECG podem permitir reidentificação. A decisão deve considerar esse risco e o consentimento dado no TCLE.
- Métricas individuais só serão publicadas após avaliação documentada do risco de reidentificação e aplicação de anonimização adequada. Caso contrário, permanecem sob acesso controlado. Com n = 20, a combinação de sessão, idade, horário, qualidade do sinal e métricas pode singularizar um participante.
- Resultados agregados só serão publicados quando não permitirem singularização do participante.

## 9. Metadados e documentação

- BIDS para os dados de sessão.
- `session_log.json` por sessão, vinculado à run de auditoria (uma run por sessão): `var_r_t`, `functional_identifiable`, `dynamic_effect_degenerate`, `tau_max_degenerate` (e demais campos conforme as semanas seguintes do Guia).
- Decisões metodológicas: `docs/CHANGELOG_CIENTIFICO.md` e ADRs.
- Versões de bibliotecas fixadas em `uv.lock`.

## 10. Responsabilidades

| Papel | Quem | Responsabilidade |
|---|---|---|
| Pesquisador responsável | Davi Rosa F. | Coleta, pseudonimização, backups, eliminação, registro |
| Orientador(a) | `[PREENCHER]` | Supervisão e segunda chave de acesso |
| CEP | `[PREENCHER]` | Aprovação e acompanhamento ético |

## 11. Pendências (B8)

| Item | Decisão necessária |
|---|---|
| Local e criptografia da tabela código ↔ identidade | Instituição e orientador(a) |
| Cópias 1, 2 e externa do backup | Pesquisador |
| Prazo de eliminação na retirada (proposta: 15 dias corridos) | Orientador(a) e CEP |
| Política de compartilhamento de dados de EEG e ECG | Orientador(a) e CEP |
| Contato do encarregado de dados da instituição | Instituição |
| Avaliação de risco de reidentificação antes de publicar métricas individuais | Pesquisador e orientador(a) |
