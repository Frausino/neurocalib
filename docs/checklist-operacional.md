# Checklist Operacional — bci-calib

> Consultar antes de cada commit e ao final de cada sprint.
> Objetivo: nenhum item esquecido, pipeline sempre verde.

---

## A cada commit

```
[ ] just test-tracking        (ou just test — suite completa)
[ ] pre-commit run --all-files  (ruff, mypy, bandit, gitleaks passando)
[ ] audit.db está em .gitignore (nunca commitar o binário)
[ ] logs/schema.sql sincronizado com _DDL_TABLES/_DDL_VIEWS em audit_db.py
[ ] nenhum secret hardcoded (API key, token, senha, hash pessoal)
[ ] mensagem de commit segue Conventional Commits: tipo(escopo): descrição
```

---

## Antes de push

```
[ ] just audit-init           (4 tabelas | 5 views — GO/NO-GO da sprint)
[ ] branch correta: feature/sN-descricao (nunca push direto em main)
[ ] git log --oneline -5      (confirma que os commits fazem sentido)
[ ] git diff --stat origin/main  (nada inesperado no diff)
```

---

## Ao abrir Pull Request

```
[ ] título do PR descreve o que muda (não "update" ou "fix")
[ ] PR referencia a sprint: "Closes S2 — bci-calib v0.X.0"
[ ] CI verde no GitHub (Actions aba verde antes de mergear)
[ ] tag de versão criada: git tag vX.Y.Z && git push --tags
[ ] weekly-audit.yml não quebrado (simular com workflow_dispatch)
```

---

## Fim de sprint (sexta ou antes do merge)

```
[ ] sprints/sprint-NN.md gerado e commitado
[ ] logbook/YYYY-MM-DD.md atualizado          ← o que esqueci na S2
[ ] Definition of Done revisada linha por linha (todas as caixas marcadas)
[ ] SBOM atualizado: uv run cyclonedx-py -o sbom.json (se dependências mudaram)
[ ] pip-audit: uv run pip-audit (zero vulnerabilidades conhecidas)
[ ] tag de versão pushed: git push --tags
[ ] PR mergeado em main (após CI verde)
```

---

## Início de sprint (segunda-feira)

```
[ ] ler o card da sprint (objetivo, outputs, NÃO PROSSEGUIR SE, Definition of Done)
[ ] confirmar dependências da sprint anterior (S1 → S2 → S3...)
[ ] criar branch: git checkout -b feature/sN-descricao
[ ] verificar se há breaking changes em deps: uv sync --upgrade --dry-run
[ ] leitura da semana agendada no calendário (structlog docs, papers, etc.)
```

---

## Recorrente — toda semana (independente de sprint)

```
[ ] git pull origin main (base atualizada)
[ ] uv sync --extra dev (ambiente limpo)
[ ] weekly-audit.yml disparado manualmente se não rodou no Monday 06:00 UTC
[ ] revisar v_failed_runs: sqlite3 audit.db "SELECT * FROM v_failed_runs LIMIT 10;"
[ ] revisar v_experiment_stats: sqlite3 audit.db "SELECT * FROM v_experiment_stats;"
```

---

## Itens que NUNCA devem entrar no Git

```
[ ] audit.db
[ ] mlruns/            (MLflow local backend)
[ ] .env               (variáveis de ambiente com secrets)
[ ] *.pt / *.ckpt      (checkpoints de modelo — usar MLflow artifacts)
[ ] data/raw/          (dados brutos — usar DVC ou referência externa)
[ ] coverage.xml       (gerado pelo CI, não pelo dev)
[ ] __pycache__/
[ ] .venv/
```

---

## Comandos de emergência

```powershell
# Pipeline quebrou — identifica onde
just lint
just typecheck
uv run bandit -r src/

# Testes falhando — verbose
uv run pytest tests/ -v --tb=long

# Banco corrompido — recria do schema
Remove-Item audit.db -ErrorAction Ignore
sqlite3 audit.db ".read logs/schema.sql"
just audit-init

# Dependência com vulnerabilidade
uv run pip-audit --fix

# Segredo vazou no histórico
git filter-repo --path arquivo-com-secret --invert-paths
```

---

*Atualizar este arquivo sempre que um novo item "esquecível" aparecer.*
*Última atualização: S2 — mai/2026.*
