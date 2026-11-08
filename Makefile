.PHONY: setup test

setup:
	@bash scripts/setup.sh

test:
	@bash tests/test_setup.sh

.PHONY: test-enviei
test-enviei:
	@python3 tests/test_enviei.py
