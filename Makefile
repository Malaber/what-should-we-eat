.PHONY: test test-cov dev db init

test:
	python3 -m pytest execution/tests/ -v --tb=short

test-cov:
	python3 -m pytest execution/tests/ -v --tb=short \
		--cov=execution --cov-report=term-missing --cov-report=html

test-e2e:
	python3 -m pytest execution/tests/e2e/ -v --tb=short --screenshot=only-on-failure --video=retain-on-failure --output=test-results

test-e2e-mobile:
	python3 -m pytest execution/tests/e2e/ -v --tb=short --device="iPhone 13" --screenshot=only-on-failure --video=retain-on-failure --output=test-results

dev:
	uvicorn execution.api.main:app --reload --port 8000

db:
	docker compose up -d

init:
	python3 -m execution.db.init_db
