.PHONY: lint test

check_dirs := .

lint:
	ruff check $(check_dirs) --fix
	ruff format $(check_dirs)

test:
	uv run -m pytest -s -v