SPEC_PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

.PHONY: validate test check e2e
validate:
	$(SPEC_PYTHON) scripts/validate_spec.py

test:
	cargo test --workspace --locked
	cargo test --workspace --locked --release
	$(SPEC_PYTHON) -m unittest discover -s scripts -p 'test_*.py'
	$(SPEC_PYTHON) -m unittest discover -s tests -p 'test_*.py'

# Full solver/native gate; use an authorized compute host for substantive work.
e2e:
	$(SPEC_PYTHON) scripts/run_e2e.py

check: validate test
	cargo fmt --all --check
	cargo clippy --workspace --all-targets --locked -- -D warnings
