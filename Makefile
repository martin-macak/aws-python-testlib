SHELL := /bin/bash
MAKE := make

TESTS ?= unit

all: build

build: poetry.lock dist/*.whl
	@poetry install

poetry.lock: pyproject.toml
	@poetry lock

dist/*.whl: poetry.lock
	@poetry dynamic-versioning && \
	@poetry build

publish:
	@if [[ ! -d './dist' ]]; then >&2 echo 'No dist found'; exit 1; fi
	@poetry run twine upload --repository pypi dist/*.whl

test:
	@pytest tests -m $(TESTS)

clean:
	@rm -rf ./dist

.PHONY: publish
.PHONY: clean
.PHONY: test