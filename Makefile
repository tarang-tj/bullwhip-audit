PY := .venv/bin/python
.PHONY: refresh registry grid numbers memo page lint test reconcile check-memo probe gate all

refresh:     ## download the current vintage of every series (networked)
	$(PY) -c "from src.bullwhip.registry import build; build(refresh=True)"
registry:    ## rebuild data/registry.csv with live FRED titles (networked, cached data)
	$(PY) -m src.bullwhip.registry
grid:
	$(PY) -m src.bullwhip.grid
numbers: grid
	$(PY) -m src.bullwhip.findings
memo: numbers
	$(PY) -m src.bullwhip.memo
page: memo
	$(PY) -m src.bullwhip.page
lint:
	.venv/bin/ruff check src tests
test:
	$(PY) -m pytest -q
reconcile:   ## independent csv+numpy recompute of headline ratios, plus raw-file hashes
	$(PY) -m src.bullwhip.reconcile
check-memo:  ## every number in the memo comes from outputs/numbers.csv
	$(PY) -m src.bullwhip.memo check
probe:       ## Playwright: 1440 and 375 px, no errors, no requests, no h-scroll, charts drawn
	$(PY) -m src.bullwhip.probe
gate: lint test reconcile check-memo probe
all: page gate
