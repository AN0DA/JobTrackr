.PHONY: lint mypy test sync migrate revision pyinstaller clean-pyinstaller

all: lint mypy test

lint:
	uv run ruff format src/ test \
	&& uv run ruff check --fix --show-fixes src/ test/

mypy:
	uv run mypy src/ test/

test:
	PYTHONPATH=$(PWD) uv run pytest --cov --cov-report term-missing:skip-covered --tb=short

sync:
	uv sync --all-groups


# Create a new migration revision
revision:
	@read -p "Enter migration message: " message; \
	python -m scripts.migration_manager --revision "$$message"

# Run database migrations
migrate:
	python -m scripts.migration_manager

pyinstaller:
	pyinstaller ./JobTrackr.spec
clean-pyinstaller:
	rm -rf build dist

