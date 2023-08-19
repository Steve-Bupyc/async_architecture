lint:
	poetry run isort . --check-only --diff
	poetry run black . --check --diff --color
	poetry run flake8 . --toml-config ./pyproject.toml
	