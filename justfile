set shell := ["powershell.exe", "-Command"]
export PYTHONPATH := "src"
default:
    just --list

sync:
    uv sync --all-extras

lint:
    uv run pre-commit run --all-files

fix:
    uv run ruff check . --fix

format:
    uv run ruff format .

typecheck:
    uv run mypy src

test:
    uv run pytest --cov=src --cov-report=term-missing -q

security:
    uv run bandit -r src

audit:
    uv run pip-audit

sbom:
    uv run cyclonedx-py environment --output-format JSON --outfile sbom.json
    Write-Host "SBOM gerado em sbom.json"

all:
    just fix
    just format
    just typecheck
    just test
    just lint

ci:
    just all

mlflow-ui:
    uv run mlflow ui --port 5001

clean:
    if (Test-Path ".coverage") { Remove-Item .coverage -Force }
    if (Test-Path "coverage.xml") { Remove-Item coverage.xml -Force }
    if (Test-Path "htmlcov") { Remove-Item htmlcov -Recurse -Force }
    if (Test-Path "sbom.json") { Remove-Item sbom.json -Force }

    Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force

help:
    just --listjust --list

audit-init:
    uv run python -c "from bci_calib.infrastructure.tracking.audit_db import AuditDB; db = AuditDB('audit.db'); db.initialise(); assert db.table_count() == 4; assert db.view_count() == 5; print(f'OK: {db.table_count()} tables | {db.view_count()} views')"

test-tracking:
    uv run pytest tests/tracking/ -v --tb=short

