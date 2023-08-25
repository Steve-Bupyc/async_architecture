run:
	uvicorn src.main:app --host 0.0.0.0 --port 8082 --reload
run-consumer:
	python3 -m src.consumer
run-scheduler:
	python3 -m src.scheduler
lint:
	poetry run isort . --check-only --diff
	poetry run black . --check --diff --color
	poetry run flake8 . --toml-config ./pyproject.toml
