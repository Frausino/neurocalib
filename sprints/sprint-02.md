# Sprint 02 — Logging, AuditDB e Correlation IDs

**Projeto:** bci-calib
**Período:** 10–14/ago/2026
**Branch:** `feature/s2-tracking-infrastructure`
**Tag:** `v0.2.0`
**Status:** CONCLUÍDA

---

## Objetivo

Rastreabilidade completa de experimentos via três planos simultâneos:
structlog (contextvars) + SQLite AuditDB + MLflow tags, conectados por um
Correlation ID (Identificador de Correlação, CID) único por execução.

Fundamento: em 12 meses de experimentos, sem rastreabilidade não é possível
saber qual versão do código produziu qual resultado. O CID é o fio que
aparece no log structlog, no MLflow, no SQLite e no commit Git.

---

## Definition of Done — Verificação

| Critério | Status | Evidência |
|---|---|---|
| `audit.db` com 4 tabelas | PASS | `just audit-init` → `OK: 4 tables` |
| `audit.db` com 5 views | PASS | `just audit-init` → `5 views` |
| `logs/schema.sql` no Git (não `audit.db`) | PASS | arquivo commitado, `audit.db` em `.gitignore` |
| Correlation ID formato correto | PASS | `exp_{gitHash}_{ts}_{uid4}` validado por regex em 10 chamadas |
| MLflow UI funcional | PASS | `just mlflow-ui` → `localhost:5001` |
| Testes unitários passando | PASS | 38/38 (`pytest tests/tracking/`) |
| CI verde (pre-commit hooks) | PASS | ruff, mypy, bandit, gitleaks: todos passando |
| `weekly-audit.yml` criado | PASS | `.github/workflows/weekly-audit.yml` |
| Logbook atualizado | PENDENTE | registrar manualmente em `logbook/` |

**Critério de aceite:** `audit.db` ✓ | `Correlation ID` ✓ | `MLflow UI` ✓

---

## Outputs Entregues

### Arquivos novos

```
src/bci_calib/infrastructure/
  tracking/
    __init__.py            — re-exporta configure_logging, AuditDB, generate_correlation_id, MLflowTracker
    logger.py              — configure_logging(): structlog 24+, silencia mne/moabb, ConsoleRenderer/JSONRenderer
    audit_db.py            — AuditDB: SQLite STRICT + WAL, 4 tabelas, 5 views, suporte :memory:
    mlflow_tracker.py      — generate_correlation_id(), MLflowTracker.start_run() com bind contextvars

logs/
  schema.sql               — DDL versionado no Git (audit.db excluído via .gitignore)

.github/workflows/
  weekly-audit.yml         — CI semanal: assert 4 tabelas/5 views + pytest tests/tracking/

tests/tracking/
  __init__.py
  test_logger.py           — 7 testes para configure_logging()
  test_audit_db.py         — 22 testes: schema, CRUD, 5 views, CHECK constraint
  test_mlflow_tracker.py   — 9 testes: formato CID, unicidade, fallback nogit
```

### Arquivos modificados

```
pyproject.toml             — packages: adicionado "src/infrastructure" (hatchling)
                           — mypy override: disallow_untyped_decorators = false em tests.*
justfile                   — export PYTHONPATH := "src"
                           — receitas: audit-init, test-tracking, mlflow-ui (porta 5001)
```

---

## Schema AuditDB

### Tabelas (4)

| Tabela | Responsabilidade |
|---|---|
| `experiment` | Registro de experimentos com nome único |
| `run` | Execução individual com `correlation_id`, `git_hash`, `status` |
| `metric` | Métricas escalares por run (kappa, accuracy, step) |
| `artifact` | Caminhos de artefatos produzidos por cada run |

### Views (5)

| View | Responsabilidade |
|---|---|
| `v_run_experiment` | Join plano de `run` + `experiment` |
| `v_latest_runs` | 50 runs mais recentes ordenados por `started_at DESC` |
| `v_run_metrics` | Métricas com contexto do run |
| `v_failed_runs` | Subset de runs com `status = 'failed'` |
| `v_experiment_stats` | Agregados por experimento (total, finished, failed, running) |

### PRAGMA WAL

`PRAGMA journal_mode = WAL` habilitado em databases de arquivo. Permite
leitores concorrentes sem bloquear escritas — crítico quando o pipeline de
calibração escreve métricas enquanto um processo de monitoramento consulta
as views.

---

## Correlation ID

**Formato:** `exp_{gitHash}_{ts}_{uid4}`

| Campo | Largura | Fonte |
|---|---|---|
| `gitHash` | 7 chars | `git rev-parse --short=7 HEAD` via `shutil.which("git")` |
| `ts` | 15 chars | UTC timestamp `YYYYMMDDTHHMMSS` |
| `uid4` | 4 chars | Primeiros 4 hex chars de UUID4 |

**Exemplo:** `exp_a1b2c3d_20260810T143022_f4e2`

**Três planos de rastreabilidade:**
1. structlog — `bind_contextvars(correlation_id=cid)` propaga para todo log da thread
2. SQLite — coluna `correlation_id` na tabela `run`
3. MLflow — tag `bci.correlation_id` em cada run

**Fallback:** `shutil.which("git")` retorna `None` fora de repositórios Git,
produzindo `exp_nogit_{ts}_{uid4}` sem lançar exceção.

---

## Testes — Cobertura

```
tests/tracking/test_logger.py        7 testes
  - silencia mne e moabb para WARNING
  - aceita log_level="DEBUG"
  - renderer="json" sem exceção
  - idempotente em chamadas repetidas
  - get_logger() funcional após configuração

tests/tracking/test_audit_db.py     22 testes
  - 4 tabelas, 5 views (nomes exatos)
  - WAL journal mode em arquivo (fixture file_db com tmp_path)
  - FK habilitado (PRAGMA foreign_keys = 1)
  - CRUD completo: insert_experiment/run, log_metric/artifact, finish_run
  - CHECK constraint rejeita status inválido (IntegrityError)
  - INSERT OR IGNORE em experiment duplicado
  - Todas as 5 views: dados corretos, filtros, joins, ordering determinístico

tests/tracking/test_mlflow_tracker.py  9 testes
  - Formato CID via regex: ^exp_([0-9a-f]{7}|nogit)_\d{8}T\d{6}_[0-9a-f]{4}$
  - Unicidade em 10 chamadas consecutivas
  - Prefixo "exp_" garantido
  - 3 segmentos após "exp_"
  - uid4 com 4 chars hex
  - ts parseável como %Y%m%dT%H%M%S e recente (delta < 60s)
  - _git_short_hash: 7 chars hex ou "nogit"
  - fallback "nogit" via monkeypatch de subprocess.run

Total: 38/38 PASSED
```

---

## Bugs Encontrados e Corrigidos

| Bug | Causa | Correção |
|---|---|---|
| `ModuleNotFoundError: infrastructure` | Arquivos colocados em `src/bci_calib/infrastructure/` em vez de `src/infrastructure/` | Mantida estrutura Clean Architecture; imports atualizados para `bci_calib.infrastructure.*` |
| `table_count()` retornava 5 | `AUTOINCREMENT` cria `sqlite_sequence` interna visível no `sqlite_master` | `AND name NOT LIKE 'sqlite_%'` na query |
| `journal_mode() == 'memory'` em `:memory:` | WAL não suportado em bancos in-memory pelo SQLite | Fixture `file_db(tmp_path)` para o teste de WAL; `:memory:` usa conexão compartilhada única |
| `ModuleNotFoundError` com `AuditDB(':memory:')` | Cada `sqlite3.connect(':memory:')` cria banco independente; conexão nova por chamada apagava tabelas | `__init__` mantém `self._memory_conn` compartilhada para `_is_memory = True` |
| Typo `ppackages` no pyproject.toml | Erro de digitação manual ao aplicar patch | Corrigido para `packages` |
| `test_v_latest_runs_ordering` não-determinístico | `DEFAULT (strftime('now'))` tem precisão de 1 segundo; 3 inserts rápidos colidiram | Timestamps explícitos injetados via `INSERT ... VALUES (?, ?, ?, ?, ts)` |
| Ruff E501 em 4 locais | Linhas > 88 chars em docstring e queries SQL | Quebra vertical de argumentos e concatenação de strings SQL |
| mypy `[misc]` em fixtures | `@pytest.fixture` sem generics completos nos stubs; `disallow_untyped_decorators=true` do `strict` | `# type: ignore[misc]` nas duas fixtures |
| Bandit B603/B607 em `_git_short_hash` | `subprocess.run(["git", ...])` com path parcial | `shutil.which("git")` resolve path completo; `# nosec B603` com justificativa |

---

## Decisões de Arquitetura

**Conexão compartilhada para `:memory:`**
Cada `sqlite3.connect(":memory:")` cria um banco independente. A classe
`AuditDB` detecta `db_path == ":memory:"` e mantém `self._memory_conn`
viva durante toda a vida do objeto, garantindo que `initialise()` e as
chamadas subsequentes enxerguem o mesmo banco.

**WAL apenas em arquivo**
PRAGMA `journal_mode = WAL` é silenciosamente ignorado pelo SQLite em
bancos in-memory (retorna `'memory'`). O teste de WAL usa `tmp_path` do
pytest para garantir um banco de arquivo real.

**shutil.which para subprocess seguro**
`subprocess.run(["git", ...])` com path parcial é vulnerável a PATH
hijacking (B607). `shutil.which("git")` resolve o executável completo
antes da chamada, eliminando a superfície de ataque. Fallback `"nogit"`
cobre ambientes sem Git no PATH.

**Porta 5001 para MLflow UI**
Porta 5000 ocupada no ambiente de desenvolvimento. Mitigação: `just mlflow-ui`
usa `--port 5001`. Risco classificado como baixa severidade / baixa probabilidade.

---

## Leitura da Semana (referências consultadas)

- structlog 24.x docs, contextvars: https://www.structlog.org/en/stable/contextvars.html
- SQLite WAL mode: https://www.sqlite.org/wal.html
- SQLite STRICT tables: https://www.sqlite.org/stricttables.html
- SQLite json_extract(): https://www.sqlite.org/json1.html
- MLflow tracking API: https://mlflow.org/docs/latest/tracking.html
- RFC 4122 (UUID4): https://www.rfc-editor.org/rfc/rfc4122#section-4.4

---

## Próxima Sprint — S3 (pré-visualização)

Fase 1 continua. Tópicos prováveis baseados na progressão do projeto:

- Pipeline de calibração conectado ao AuditDB
- Primeiros experimentos com dados MOABB (BCI Competition IV 2a)
- Integração EEGNet/ATCNet com MLflowTracker
- Relatório PDF automático (Sub-PIC 3 — módulo ReportLab)

---

*Gerado em 18/mai/2026. Branch: `feature/s2-tracking-infrastructure`. Tag: `v0.2.0`.*
