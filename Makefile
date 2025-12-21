SHELL := /bin/zsh

.PHONY: init sync up down logs fmt lint type test run

init:
	@command -v uv >/dev/null 2>&1 || (echo "uv not found. Install it first (brew install uv)"; exit 1)
	uv sync

sync:
	uv sync

run:
	uv run uvicorn backend.app.main:app --reload

up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f

fmt:
	uv run black .

lint:
	uv run ruff check .

type:
	uv run mypy backend/app

test:
	uv run pytest -q

db-up:
	docker compose up -d db

db-down:
	docker compose down -v

db-reset:
	docker compose down -v
	docker compose up -d db

stop:
	@lsof -ti tcp:8000 | xargs -r kill -9 || true