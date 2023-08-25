run:
	uvicorn src.main:app --host 0.0.0.0 --port 8081 --reload

run-consumer:
	python3 -m src.consumer
lint:
	poetry run isort . --check-only --diff
	poetry run black . --check --diff --color
	poetry run flake8 . --toml-config ./pyproject.toml
