# Results Provenance

Log of which git commit produced which numbers cited in the manuscript.
`data/` and `outputs/` are gitignored (regenerable); this file is the link
between a reported number and the exact code that produced it.

| Date | Commit | Script(s) run | Numbers produced | Cited where |
|---|---|---|---|---|
| 2026-07-08 | 38c62a8 | 01_extract_cohort.py | Candidate cohort N=2,824 (from 6,388 total; -0 dept, -65 age<18, -3,458 opdur<=120min, -41 reoperation) | STROBE Fig 1 (candidate-cohort branch only — final N pending 02) |
| 2026-07-08 | 56dc9f1 | 02_build_exposures.py | Final analytic cohort N=2,568 (candidate 2,824 minus 75 no_valid_bt, 1 empty-window, 180 failed trimmed-95% coverage). Coverage pass rate 93.4% (2,568/2,748 with valid BT data). Pre-monitoring gap: median 1,480s, 62.5% <=30min. | STROBE Fig 1 (final N), SS4 coverage-rule text |
| 2026-07-08 | 56dc9f1 | 02b_coverage_bias_check.py | Stomach-surgery coverage-failure OR=6.62 (95% CI 4.84-9.05, Fisher p=8.2e-32), survives duration/approach/position adjustment (adjusted OR=0.213 for passing, p=9.6e-12). No differential attrition by EBL overall (p=0.298) or within-Stomach (p=0.735). Excluded-vs-included table in outputs/tables/excluded_vs_included_comparison.csv. | SS3 (yield note), SS10 (limitations), excluded-vs-included supplementary table |
| 2026-07-09 | 6192908 | 02c_aim4_cohort.py | CONFIRMED final analytic cohort N=2,568 (read directly from final_exposure_cohort.parquet, matches prior arithmetic exactly). Aim 4 cohort (analytic AND MAP trimmed coverage >=95%, i.e. arterial-line subset) N=1,951 (76.0% of analytic cohort). Of candidates with any MAP data at all, 98.8% clear trimmed>=95% -- the constraint is a-line placement (23.1% have zero MAP data), not MAP signal dropout when present. NOTE: Aim 4 subsequently deferred to a future paper (see chat log) -- numbers retained for that future use, not this manuscript. | SS4 (Cohort N statements); Aim 4 deferred, not cited in this manuscript |
| 2026-07-09 | ee7d5df | 03_build_outcomes.py | outcomes.parquet, N=2,568. Completeness: EBL 83.3%, transfused 100%, delta_ptinr/aptt/fib 47.0%/46.8%/44.5% (lower than postop-only yield since both preop AND postop values now required), delta_hb 69.7%, aki_stage 82.5% (449 missing both windows), LOS/icu_days/death_inhosp ~100%. AKI stage distribution (corrected): 0=1915, 1=134, 2=24, 3=46, NaN=449. 2 cases nulled for dis<opend raw-data anomaly (caseid 409, 1807). | SS6 (Outcome definitions/completeness), Table 1/2 supplementary yield rows |
