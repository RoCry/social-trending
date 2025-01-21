.PHONY: lint test download_db

check_dirs := .

lint:
	ruff check $(check_dirs) --fix
	ruff format $(check_dirs)

test:
	uv run -m pytest -s -v

download_db:
	# Download the latest social.sqlite database from GitHub releases
	@curl -L https://github.com/RoCry/social-trending/releases/download/latest/social.sqlite -o cache/social.sqlite
