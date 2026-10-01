SPEC_PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

.PHONY: validate test check
validate:
	$(SPEC_PYTHON) scripts/validate_spec.py

test:
	cargo test --workspace --locked
	cargo test --workspace --locked --release
	$(SPEC_PYTHON) -m unittest discover -s scripts -p 'test_*.py'

check: validate test
	cargo fmt --all --check
	cargo clippy --workspace --all-targets --locked -- -D warnings
