VARS_OLD := $(.VARIABLES)

SHELL := /bin/bash
MAKE := make

BUILD_DIR := dist


all: build

build: $(BUILD_DIR)/*.whl
	@poetry install

dist/*.whl:
	@poetry dynamic-versioning
	@poetry build

publish:
	@if [[ ! -d './dist' ]]; then >&2 echo 'No dist found'; exit 1; fi
	@poetry run twine upload --repository pypi dist/*.whl

test:
	@pytest tests

clean:
	@rm -rf $(BUILD_DIR)

debug:
	$(foreach v,                                        \
		  $(filter-out $(VARS_OLD) VARS_OLD,$(.VARIABLES)), \
		  $(info $(v) = $($(v))) \
	)

.PHONY: clean test publish debug
