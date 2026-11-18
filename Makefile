# One-command checks for QuantLab. Run from the repository root with the project's virtual environment active.
#   make check   : every frozen manifest still matches its files, then all unit tests pass
#   make charts  : redraw the README charts and the Stage 6 charts from the saved results
#   make demo    : run the H1 tool on the synthetic demo file (no market data needed)
PY ?= python

.PHONY: check manifests test charts dashboard demo

check: manifests test

manifests:
	$(PY) scripts/verify_manifests.py

test:
	$(PY) -m pytest -q

charts:
	$(PY) scripts/make_readme_charts.py
	$(PY) scripts/make_stage6_charts.py

dashboard:
	$(PY) dashboard/build_dashboard.py

demo:
	PYTHONPATH=src $(PY) -m quantlab.h1tool examples/synthetic_demo.csv
