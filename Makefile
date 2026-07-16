# LCS CRM · common development commands.
# Use `make help` to list targets. Each target is a thin wrapper so that
# contributors have a single, memorable entry point regardless of OS.

SHELL := /usr/bin/env bash
.SHELLFLAGS := -euo pipefail -c
.DEFAULT_GOAL := help

SITE ?= crm.lcs.local

.PHONY: help bootstrap install-app test test-py test-frontend test-e2e \
        lint lint-py lint-frontend build-image scan-image protect-branches

help: ## Show this help
	@awk 'BEGIN{FS=":.*##"}/^[a-zA-Z_-]+:.*##/{printf "  \033[36m%-18s\033[0m %s\n",$$1,$$2}' $(MAKEFILE_LIST)

bootstrap: ## One-shot WSL2 dev environment
	./scripts/bootstrap_wsl.sh

install-app: ## Install / update lcs_integrations on local bench
	./scripts/install_lcs_app.sh

test: test-py test-frontend ## Run all fast tests (no e2e)

test-py: ## Pytest with coverage gate
	cd lcs_integrations && pip install -q -e ".[dev]" && pytest

test-frontend: ## Vitest with coverage gate
	cd frontend && yarn install --frozen-lockfile && yarn test:coverage

test-e2e: ## Playwright smoke against local bench
	cd e2e && yarn install --frozen-lockfile && yarn install-browsers && yarn test

lint: lint-py lint-frontend ## Lint everything

lint-py: ## Ruff + mypy for lcs_integrations
	cd lcs_integrations && ruff check . && mypy lcs_integrations || true

lint-frontend: ## ESLint for Vue code
	cd frontend && yarn lint

build-image: ## Build production Docker image
	docker build -f docker/Dockerfile -t lcs-crm:local .

scan-image: build-image ## Build + Trivy-scan the image
	trivy image --severity CRITICAL,HIGH --ignore-unfixed lcs-crm:local

protect-branches: ## Apply LCS branch protection via gh CLI
	./scripts/github_branch_protection.sh
