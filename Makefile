.PHONY: all lint test ci mlflow-ui clean help

# Alvo padrão — GO/NO-GO check do guia (Seção 0.5)
all: lint test

lint:
	uv run pre-commit run --all-files

test:
	uv run pytest --cov=src --cov-report=term-missing -q

ci: all

mlflow-ui:
	uv run mlflow ui --port 5000

sbom:
	uv run cyclonedx-py environment --output-format JSON --outfile sbom.json
	@echo "SBOM gerado em sbom.json"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .coverage coverage.xml htmlcov/ sbom.json

help:
	@echo "Alvos disponíveis:"
	@echo "  make all       — lint + test (GO/NO-GO check)"
	@echo "  make lint      — pre-commit em todos os arquivos"
	@echo "  make test      — pytest com cobertura"
	@echo "  make mlflow-ui — MLflow UI em localhost:5000"
	@echo "  make sbom      — gera SBOM CycloneDX local"
	@echo "  make clean     — remove artefatos temporários"
