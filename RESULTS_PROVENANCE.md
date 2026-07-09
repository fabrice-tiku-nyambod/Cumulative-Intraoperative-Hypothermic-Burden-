# Results Provenance

Log of which git commit produced which numbers cited in the manuscript.
`data/` and `outputs/` are gitignored (regenerable); this file is the link
between a reported number and the exact code that produced it.

| Date | Commit | Script(s) run | Numbers produced | Cited where |
|---|---|---|---|---|
| 2026-07-08 | 38c62a8 | 01_extract_cohort.py | Candidate cohort N=2,824 (from 6,388 total; -0 dept, -65 age<18, -3,458 opdur<=120min, -41 reoperation) | STROBE Fig 1 (candidate-cohort branch only — final N pending 02) |
| 2026-07-08 | PENDING (this commit) | 02_build_exposures.py | Final analytic cohort N=2,568 (candidate 2,824 minus 75 no_valid_bt, 1 empty-window, 180 failed trimmed-95% coverage). Coverage pass rate 93.4% (2,568/2,748 with valid BT data). Pre-monitoring gap: median 1,480s, 62.5% <=30min. | STROBE Fig 1 (final N), SS4 coverage-rule text |
| 2026-07-08 | PENDING (this commit) | 02b_coverage_bias_check.py | Stomach-surgery coverage-failure OR=6.62 (95% CI 4.84-9.05, Fisher p=8.2e-32), survives duration/approach/position adjustment (adjusted OR=0.213 for passing, p=9.6e-12). No differential attrition by EBL overall (p=0.298) or within-Stomach (p=0.735). Excluded-vs-included table in outputs/tables/excluded_vs_included_comparison.csv. | SS3 (yield note), SS10 (limitations), excluded-vs-included supplementary table |
