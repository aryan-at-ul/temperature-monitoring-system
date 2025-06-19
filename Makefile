.PHONY: install test api ingestion db-init lint

install:
	pip install -r requirements.txt

test:
	pytest -q

api:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

ingestion:
	python -m data_ingestion.pipeline

db-init:
	psql -h $$DB_HOST -p $$DB_PORT -U $$POSTGRES_USER -d $$POSTGRES_DB -f database/schema.sql

lint:
	rufflehog3 --fail
