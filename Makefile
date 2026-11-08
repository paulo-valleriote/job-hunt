.PHONY: setup
setup:
	@bash scripts/setup.sh

.PHONY: test
test:
	@bash tests/test_setup.sh

.PHONY: doctor
doctor:
	@bash scripts/doctor.sh

.PHONY: test-doctor
test-doctor:
	@bash tests/test_doctor.sh

.PHONY: check-config
check-config:
	@python3 scripts/validar_config.py

.PHONY: test-config
test-config:
	@python3 -m unittest tests.test_validar_config

.PHONY: test-triagem
test-triagem:
	@python3 -m unittest tests.test_triagem
  
.PHONY: test-busca
test-busca:
	@python3 -m unittest tests.test_busca
  
.PHONY: test-enviei
test-enviei:
	@python3 tests/test_enviei.py
