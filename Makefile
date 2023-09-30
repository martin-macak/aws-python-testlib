SHELL := /bin/bash
MAKE := make

VERSION ?= $(shell git describe --tags 2>/dev/null || echo "0.0.0-$$(git rev-parse --short HEAD)")

all: build

build: poetry.lock dist/*.whl
	@poetry install

poetry.lock: pyproject.toml
	@poetry lock

dist/*.whl: poetry.lock
	@export POETRY_DYNAMIC_VERSIONING_BYPASS="$(VERSION)" && \
		poetry dynamic-versioning && \
		poetry build