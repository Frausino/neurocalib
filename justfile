# justfile
# Cross-platform: sh on Linux/WSL, PowerShell on native Windows.
# Recipes call only uv/python so the same commands work in both shells.

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

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
    uv run mypy src tests

test:
    uv run pytest --cov=src --cov-report=term-missing -q

security:
    uv run bandit -c pyproject.toml -r src

audit:
    uv run pip-audit --skip-editable --ignore-vuln PYSEC-2026-3447 --ignore-vuln GHSA-xmj3-9gf7-h52w

sbom:
    uv run cyclonedx-py environment --output-format JSON --outfile sbom.json

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
    uv run python -c "import pathlib, shutil; root = pathlib.Path('.'); [p.unlink() for p in map(pathlib.Path, ['.coverage', 'coverage.xml', 'sbom.json']) if p.exists()]; [shutil.rmtree(p) for p in [root / 'htmlcov', *(d for d in root.rglob('__pycache__') if '.venv' not in d.parts)] if p.exists()]"

help:
    just --list

audit-init:
    uv run python -c "from bci_calib.infrastructure.tracking.audit_db import AuditDB; db = AuditDB('audit.db'); db.initialise(); assert db.table_count() == 4; assert db.view_count() == 5; print(f'OK: {db.table_count()} tables | {db.view_count()} views')"

test-tracking:
    uv run pytest tests/tracking/ -v --tb=short
