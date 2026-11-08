.PHONY: setup test

setup:
	@bash scripts/setup.sh

test:
	@bash tests/test_setup.sh

.PHONY: doctor test-doctor

doctor:
	@bash scripts/doctor.sh

test-doctor:
	@bash tests/test_doctor.sh
