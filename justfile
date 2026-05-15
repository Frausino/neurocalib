set shell := ["powershell.exe", "-Command"]

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
    uv run mlflow ui --port 5000

clean:
    if (Test-Path ".coverage") { Remove-Item .coverage -Force }
    if (Test-Path "coverage.xml") { Remove-Item coverage.xml -Force }
    if (Test-Path "htmlcov") { Remove-Item htmlcov -Recurse -Force }
    if (Test-Path "sbom.json") { Remove-Item sbom.json -Force }

    Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force

help:
    just --listjust --list
