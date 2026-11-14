# QuantLab H1 Results dashboard

A five-page summary of the H1 study, with one tab per page:

| Page | Contents |
|---|---|
| Overview | headline numbers and one card per real sample |
| Real data | T against the C3 limit; which periods differ |
| Simulation | simulations by stage, highest false-alarm rate, all 96 validation cells, six harder processes |
| Phase 6 | the exploratory placement result per sample |
| Checks & limits | integrity checks, what the results do not show, key terms |

Each page has its own link (for example `#p-phase6`).

- **Online version:** https://claude.ai/artifact/JyiVESsrnCvSjoXpwpdARw (private until shared)
- **Offline version:** `dashboard/index.html`. Open it in a browser. It needs an internet connection only to load D3.js v7 from cdnjs.

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
| `datasets/calibration_cells.csv` | Stage 3: C3 and old-test rejection rates in all 96 validation cells (from `outputs/milestone4/h1_calibration/stage3/report_tables/stage3_all_cells_rates.csv`) |
| `datasets/alt_processes.csv` | Stage 4: rates under six harder simulated processes per market (from `stage4/report_tables/alt_validation_cells.csv`) |
| `datasets/real_tests.csv` | The four pre-registered real-data runs (`docs/31`, `docs/35`, `docs/39`) |
| `datasets/simulation_ledger.csv` | Simulations per stage (`docs/19` §5) |
| `datasets/integrity_checks.csv` | Test-suite, manifest and data-handling checks run on 2026-11-14 |
| `datasets/phase6_summary.csv` | Exploratory Phase 6 result per real sample (`docs/41`, from `outputs/milestone4/phase6/`) |
| `build_dashboard.py` | Embeds the page and data into `index.html` |
| `index.html` | Generated standalone dashboard. Rebuild it after changing `page.html` or the datasets |

All files are aggregates of saved outputs. No raw or bar-level market data is included (Yahoo Finance terms, see `docs/03`).
