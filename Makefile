# COMMON CLI COMMANDS FOR DEVELOPMENT

.PHONY: install_deps
install_deps:
	@poetry install --with=dev,test

.PHONY: update_deps
update_deps:
	@poetry update --with=dev,test

.PHONY: test
test:
	@poetry run pytest -vv

.PHONY: itest
itest:
	@poetry run pytest -vv lab_gen/tests/integration

.PHONY: lint
lint:
	@poetry run ruff check --fix lab_gen

.PHONY: check
check:
	pre-commit run --all-files
