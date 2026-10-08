PYTHON ?= python
SMOKE_ARGS ?=

.PHONY: setup lint format test test-contract test-runtime test-graphs test-e2e smoke-hermes smoke-compose generate-contracts check-contracts build backend frontend
setup lint format test test-contract test-runtime test-graphs test-e2e generate-contracts check-contracts build backend frontend:
	$(PYTHON) scripts/dev.py $@

smoke-hermes smoke-compose:
	$(PYTHON) scripts/dev.py $@ $(SMOKE_ARGS)
