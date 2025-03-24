# COMMON CLI COMMANDS FOR DEVELOPMENT

.PHONY: install_deps
install_deps:
	@uv sync

.PHONY: update_deps
update_deps:
	@uv lock --upgrade

.PHONY: test
test:
	@uv run pytest -vv

.PHONY: itest
itest:
	@uv run pytest -vv lab_gen/tests/integration

.PHONY: lint
lint:
	@uv run ruff check --fix lab_gen

.PHONY: check
check:
	@uv run pre-commit run --all-files
