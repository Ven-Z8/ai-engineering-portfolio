.PHONY: install run demo test lint type-check setup-vault clean

install:
	uv sync --extra dev

run:
	.venv/bin/sbo run

demo:
	.venv/bin/sbo run --dry-run

setup-vault:
	.venv/bin/sbo vault setup

test:
	.venv/bin/python -m pytest tests/unit -q

lint:
	.venv/bin/ruff check src/ tests/

type-check:
	.venv/bin/mypy src/second_brain --ignore-missing-imports

add-github:
	@read -p "GitHub URL: " url; .venv/bin/sbo add github $$url

status:
	.venv/bin/sbo status

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; true
