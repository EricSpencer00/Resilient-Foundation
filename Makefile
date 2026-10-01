SPEC_PYTHON ?= python3

.PHONY: validate
validate:
	$(SPEC_PYTHON) scripts/validate_spec.py
