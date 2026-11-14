# QuantLab H1 Results dashboard

A one-page summary of the H1 study: the simulation check of the fixed critical value C3, and the real-data tests on NSE and US stocks.

- **Online version:** https://claude.ai/artifact/JyiVESsrnCvSjoXpwpdARw (private until shared)
- **Offline version:** `dashboard/index.html`. Open it in a browser. It needs an internet connection only to load d3 from cdnjs.

## Run it on localhost

```bash
python dashboard/build_dashboard.py
```
```bash
python -m http.server 8765 --directory dashboard
```

Then open http://127.0.0.1:8765/

## Files

| File | What it is |
|---|---|
| `page.html` | The dashboard page, the same one stored in the online version |
| `data/calibration_cells.csv` | Stage 3: C3 and old-test rejection rates in all 96 validation cells (from `outputs/milestone4/h1_calibration/stage3/report_tables/stage3_all_cells_rates.csv`) |
| `data/alt_processes.csv` | Stage 4: rates under six harder simulated processes per market (from `stage4/report_tables/alt_validation_cells.csv`) |
| `data/real_tests.csv` | The three pre-registered real-data runs (`docs/31`, `docs/35`) |
| `data/simulation_ledger.csv` | Simulations per stage (`docs/19` §5) |
| `data/integrity_checks.csv` | Test-suite, manifest and data-handling checks run on 2026-11-14 |
| `build_dashboard.py` | Embeds the page and data into `index.html` |
| `index.html` | Generated standalone dashboard. Rebuild it after changing `page.html` or the data |

All files are aggregates of saved outputs. No raw or bar-level market data is included (Yahoo Finance terms, see `docs/03`).
