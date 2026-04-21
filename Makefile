.PHONY: help setup run clean test lint format install-dev docker-up docker-down db-init db-migrate

help:
	@echo "QA-Buster Make Commands"
	@echo "========================"
	@echo "make setup           - Setup development environment"
	@echo "make install-dev     - Install development dependencies"
	@echo "make run             - Run the application"
	@echo "make lint            - Check code quality"
	@echo "make format          - Format code with black"
	@echo "make test            - Run tests"
	@echo "make clean           - Clean up cache files"
	@echo "make docker-up       - Start Docker containers"
	@echo "make docker-down     - Stop Docker containers"
	@echo "make db-init         - Initialize database"
	@echo "make logs            - View application logs"

setup:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	cp .env.example .env
	@echo "✓ Setup complete! Update .env with your configuration."

install-dev:
	./venv/bin/pip install -r requirements.txt
	./venv/bin/pip install black flake8 pytest pytest-asyncio

run:
	./venv/bin/python main.py

lint:
	./venv/bin/flake8 database.py ingest.py llm_worker.py main.py --max-line-length=100

format:
	./venv/bin/black database.py ingest.py llm_worker.py main.py --line-length=100

test:
	./venv/bin/pytest -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	@echo "✓ Cleaned up cache files"

docker-build:
	docker build -t qa-buster:latest .

docker-up:
	docker-compose up -d
	@echo "✓ Containers started"
	@echo "Frontend: http://localhost:8000"

docker-down:
	docker-compose down
	@echo "✓ Containers stopped"

db-init:
	./venv/bin/python -c "from database import init_db; init_db(); print('✓ Database initialized')"

logs:
	docker-compose logs -f qa-buster

requirements-freeze:
	./venv/bin/pip freeze > requirements.txt
	@echo "✓ Requirements frozen"

update-deps:
	./venv/bin/pip install --upgrade -r requirements.txt
	@echo "✓ Dependencies updated"

security-check:
	./venv/bin/pip install safety
	./venv/bin/safety check
