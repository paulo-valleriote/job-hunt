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

.PHONY: test-triagem
test-triagem:
	@python3 -m unittest tests.test_triagem

.PHONY: doctor test-doctor

doctor:
	@bash scripts/doctor.sh

test-doctor:
	@bash tests/test_doctor.sh

.PHONY: test-curriculo
test-curriculo:
	@python3 -m unittest tests.test_curriculo

.PHONY: test-avaliador
test-avaliador:
	@python3 -m unittest tests.test_avaliador

.PHONY: test-anti-invencao
test-anti-invencao:
	@python3 -m unittest tests.test_anti_invencao

.PHONY: test-enviei
test-enviei:
	@python3 tests/test_enviei.py
