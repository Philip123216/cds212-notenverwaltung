.DEFAULT_GOAL := help

.PHONY: help install run test cov lint fmt clean

help: ## Zeigt diese Hilfe an
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## Installiert alle Abhängigkeiten
	pip install -r requirements-dev.txt

run: ## Startet den Entwicklungsserver auf Port 8000
	flask --app wsgi run --debug --port 8000

test: ## Führt die Testsuite aus
	pytest

cov: ## Führt Tests mit Coverage-Bericht aus (Gate: 80%)
	pytest --cov=app --cov-report=term-missing

lint: ## Prüft Code-Stil und Formatierung mit Ruff
	ruff check .
	ruff format --check .

fmt: ## Formatiert den Code automatisch
	ruff check --fix .
	ruff format .

clean: ## Entfernt temporäre Caches
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov
	find . -name __pycache__ -type d -exec rm -rf {} +
