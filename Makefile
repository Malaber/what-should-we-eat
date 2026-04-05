.PHONY: test test-cov dev db init

test:
	python3 -m pytest execution/tests/ -v --tb=short

test-cov:
	python3 -m pytest execution/tests/ -v --tb=short \
		--cov=execution --cov-report=term-missing --cov-report=html

dev:
	uvicorn execution.api.main:app --reload --port 8000

db:
	docker compose up -d

init:
	python3 -m execution.db.init_db
