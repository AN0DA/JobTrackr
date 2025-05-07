.PHONY: lint mypy test sync migrate revision

all: lint mypy test

lint:
	uv run ruff format src/ \
	&& uv run ruff check --fix --show-fixes src/

mypy:
	uv run mypy src/

test:
	PYTHONPATH=$(PWD) uv run pytest --cov --cov-report term-missing:skip-covered

sync:
	uv sync --all-groups

dump:
	./dump.sh src src.dump

# Create a new migration revision
revision:
	@read -p "Enter migration message: " message; \
	python -m scripts.migration_manager --revision "$$message"

# Run database migrations
migrate:
	python -m scripts.migration_manager
