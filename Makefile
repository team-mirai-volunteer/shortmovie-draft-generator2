TARGET ?= src tests
TEST_TARGET ?= tests
MYPY_TARGET ?= src tests

lint:
	uv run ruff check ${TARGET}
	uv run mypy ${MYPY_TARGET}

fmt:
	uv run ruff check ${TARGET} --fix-only --exit-zero
	uv run ruff format ${TARGET}

test:
	uv run pytest -v ${TEST_TARGET}
