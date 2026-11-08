.PHONY: setup test doctor test-doctor check-config test-config \
	test-busca test-triagem test-curriculo test-avaliador \
	test-anti-invencao test-enviei ui test-ui

setup:
	@bash scripts/setup.sh

test:
	@bash tests/test_setup.sh

doctor:
	@bash scripts/doctor.sh

test-doctor:
	@bash tests/test_doctor.sh

check-config:
	@python3 scripts/validar_config.py

test-config:
	@python3 -m unittest tests.test_validar_config

test-busca:
	@python3 -m unittest tests.test_busca

test-triagem:
	@python3 -m unittest tests.test_triagem

test-curriculo:
	@python3 -m unittest tests.test_curriculo

test-avaliador:
	@python3 -m unittest tests.test_avaliador

test-anti-invencao:
	@python3 -m unittest tests.test_anti_invencao

test-enviei:
	@python3 tests/test_enviei.py

ui:
	@python3 -m streamlit run ui/app.py --server.address localhost --server.headless true

test-ui:
	@python3 -m unittest tests.test_ui_vagas

.PHONY: test-ui-curriculos
test-ui-curriculos:
	@python3 -m unittest tests.test_ui_curriculos
