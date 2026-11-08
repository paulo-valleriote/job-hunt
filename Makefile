.PHONY: setup
setup:
	@bash scripts/setup.sh

.PHONY: test
test:
	@bash tests/test_setup.sh

.PHONY: check-config
check-config:
	@python3 scripts/validar_config.py

.PHONY: test-config
test-config:
	@python3 -m unittest tests.test_validar_config
  
.PHONY: test-enviei
test-enviei:
	@python3 tests/test_enviei.py
