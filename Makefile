create-dev:
	pre-commit install
	pre-commit autoupdate
	uv sync
	uv build
