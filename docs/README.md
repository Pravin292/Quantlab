# Documentation index

Documents are numbered in reading order. `07_research_protocol.md` does not exist: **docs 09 to 24 are diagnostic or planning documents, not a frozen research protocol.**

## M1 to M3: data, pipeline and EDA

| Doc | Content |
|---|---|
| [01](01_data_availability_report.md) | Data availability report |
| [02](02_research_spec.md) | Data requirements, hypotheses, screening, assumptions |
| [03](03_data_sources_and_licensing.md) | Data sources and licensing (why the market data is not in this repository) |
| [04](04_nse_anomaly_investigation.md) | NSE anomaly investigation |
| [05](05_validation_rules.md) | Validation and cleaning rules |
| [06](06_eda_findings.md) | Exploratory data analysis findings |
| [07](07_test_registry.csv) | Registry of planned tests (hypothesis, class, family, market) |

## M4a and M4b: H1 and H2 diagnostics (simulated data)

| Doc | Content |
|---|---|
| [09](09_m4a_h1_h2_diagnostic_report.md) | H1 and H2 calibration failures |
| [10](10_m4a_h1_method_comparison_and_h2_validation.md) | H1 method comparison (RMS estimand), H2 validation |
| [11](11_m4a_next_diagnostic_round.md) | Next diagnostic round (calibration, dependence, D5, H2 on US) |
| [12](12_m4b_h1_inference_and_h2_power_report.md) | M4b H1 inference and H2 power: final audit report |

## H1 calibration investigation

| Doc | Content |
|---|---|
| [13](13_h1_calibration_investigation_plan.md) | Diagnosis, options and staged plan |
| [14](14_h1_calibration_stage0_report.md) | Stage 0 report (preparation only) |
| [15](15_h1_calibration_decision_document.md) | Decision document before Stage 1 (definitions of C1 to C3, gates) |
| [15a](15a_h1_calibration_spec_v1_1.md) | Specification v1.1: change log, definitions, gates |
| [15b](15b_h1_calibration_v1_1_review_record.md) | Review record for v1.1 and the Stage 1 launch |
| [16](16_h1_calibration_stage1_report.md) | Stage 1 report |
| [17](17_h1_calibration_stage2_plan.md) | Stage 2 plan |
| [17b](17b_h1_calibration_stage2_review_record.md) | Stage 2 design decisions: review record |
| [17c](17c_h1_calibration_stage2_d2_confirmation.md) | D2 diagnostic flag: confirmed formula, units and labels |
| [18](18_h1_calibration_stage2_report.md) | **Stage 2 report** (all results, failures, violations, borderline flags) |
| [20](20_h1_calibration_stage3_prerun_record.md) | Stage 3 pre-run record: authorisation, frozen specification, fill-ins, run-once rule |
| [21](21_h1_calibration_stage3_report.md) | **Stage 3 report** (locked validation of C3; all cells, D2 flags, power cells, Stage 4/5 dependency chain) |
| [22](22_h1_calibration_stage4_preregistration.md) | Stage 4 preregistration (null check, alternative processes, bar-level check, reference check, decisions D1–D6) |
| [22b](22b_h1_calibration_stage4_approval_record.md) | Stage 4 approval record (D1–D6 approvals, 8,000 simulations per bar-level cell, fill-ins) |
| [23](23_h1_calibration_stage4_report.md) | **Stage 4 report** (independent validation of C3: all five preregistered criteria met; limitations) |
| [24](24_h1_calibration_stage5_decision_report.md) | **Stage 5 decision report** (classification PARTIAL; validated domain, count and seed audit, gate interpretation, limitations). Numbered 24 because `docs/14` is the Stage 0 report |
| [25](25_h1_calibration_stage5_errata.md) | Stage 5 errata (repeat-variability re-analysis of saved Stage 2 and 3 files; PARTIAL unchanged) |
| [26](26_real_data_descriptive_validation_protocol.md) | **Phase 6 protocol, revision 5: PROPOSED, not approved, not executed** (real-data descriptive validation; no data accessed) |
| [27](27_quantlab_formal_decision_and_approval_register.md) | Phase 6 decision and approval register (D1–D17 all pending; gates, checklist, blocked work) |
| [28](28_stage0_mode_b_reference_layout_verification.md) | Stage 0 reference layout check for Mode B (read-only; the n = 59 D-tail claim is not supported) |
| [29](29_stage0_d_tail_compatibility_decision_memo.md) | Decision memo on the Stage 0 D-tail mismatch (options A, B, C; owner decision pending) |
| [30](30_real_data_h1_test_preregistration_plan.md) | Real-data H1 test pre-registration plan (frozen C3, existing local sample; R1–R8, authorisation record) |
| [31](31_real_data_h1_test_report.md) | **Real-data H1 test report** (US: T = 22.59, reject; NSE: not testable, 58 complete sessions) |
| [32](32_decision_sheet_and_next_paths.md) | Decision sheet: paths P1–P3 and a suggested response to D1–D17 per path (nothing approved) |
| [33](33_complete_h1_check_preregistration_plan.md) | Path P2 pre-registration plan: repeat the H1 check on new data (NSE and fresh US); proposed, blocked on provider and licence |
| [34](34_provider_research_for_p2.md) | Provider research for the P2 check (NSE: Kite Connect, TrueData; US: Alpaca, Databento, Massive); web research, unverified terms |
| [35](35_nse_h1_check_report.md) | **NSE H1 check report** (zero-cost, one Yahoo pull: 59 complete sessions, T = 17.31, reject) |
| [36](36_project_summary_in_plain_language.md) | **Plain-language project summary** (question, method, results, limits, what is left) |
| [37](37_fresh_us_check_design.md) | Fresh-US check design (Alpaca free plan, window before 2026-08-06), frozen before any fetch; awaiting keys |
| [38](38_closing_decisions_and_status.md) | **Closing decisions and final status**: re-test results, D-tail Option A, Phase 6 shelved, Alpaca pending |
| [39](39_fresh_us_check_report.md) | **Fresh-US check report**: Alpaca SIP, 2026-04-13 to 2026-07-07, T = 17.75, reject |
| [40](40_phase6_protocol_revision6_exploratory.md) | Phase 6 protocol revision 6 (exploratory, Option A), frozen before measurement; records the shape-E variance/volatility finding |
| [41](41_phase6_exploratory_report.md) | **Phase 6 exploratory report**: NSE blocks INSUFFICIENT, US first CANNOT BE CLASSIFIED, US fresh OUTSIDE (dependence) |

## Project status

| Doc | Content |
|---|---|
| [19](19_quantlab_project_status_report.md) | **Consolidated project status**, findings, limitations, simulation ledger, integrity checks and blockers |

Doc 12 is a closed audit report and is not edited; later documents refine its wording where needed (docs 13 section 2.1).
