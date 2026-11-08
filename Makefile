.PHONY: setup test

setup:
	@bash scripts/setup.sh

test:
	@bash tests/test_setup.sh

.PHONY: check-config test-config
check-config:
	@python3 scripts/validar_config.py

test-config:
	@python3 -m unittest tests.test_validar_config
