"""
Extends outputs/tables/excluded_vs_included_comparison.csv (from 02b) with
AKI and coagulation outcomes, per SS3b's last open item. This requires
outcomes for the EXCLUDED 256 cases too, which 03_build_outcomes.py never
computed (it only ran on the final N=2,568 analytic cohort) -- so this
script reapplies the same lab-lookup/KDIGO logic from 03 across the full
candidate cohort (N=2,824), not just the included subset.

Small deliberate duplication of get_lab_value/stage_kdigo from
03_build_outcomes.py rather than importing across a leading-digit filename.
Logic must stay in sync with 03 by hand if either changes.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = PROJECT_DIR.parent / "DATASET"
TABLES_DIR = PROJECT_DIR / "outputs" / "tables"

DAY = 86400
HOUR = 3600
PREOP_LOOKBACK_SEC = 90 * DAY


def get_lab_value(cohort, lab, lab_name, anchor_col, window_start_sec, window_end_sec, agg="first"):
    subset = lab.loc[lab["name"] == lab_name, ["caseid", "dt", "result"]]
    m = cohort[["caseid", anchor_col]].merge(subset, on="caseid", how="left")
    m["delta"] = m["dt"] - m[anchor_col]
    m = m[(m["delta"] >= window_start_sec) & (m["delta"] <= window_end_sec)]
    if agg == "first":
        m = m.sort_values(["caseid", "dt"]).drop_duplicates("caseid", keep="first")
    elif agg == "last":
        m = m.sort_values(["caseid", "dt"]).drop_duplicates("caseid", keep="last")
    elif agg == "max":
        idx = m.groupby("caseid")["result"].idxmax()
        m = m.loc[idx]
    else:
        raise ValueError(f"unknown agg: {agg}")
    out = m.set_index("caseid")["result"]
    return out.reindex(cohort["caseid"]).values


def stage_kdigo(preop_cr, peak_48h, peak_7d):
    if pd.isna(preop_cr) or (pd.isna(peak_48h) and pd.isna(peak_7d)):
        return np.nan
    stage_48h = 1 if (pd.notna(peak_48h) and (peak_48h - preop_cr) >= 0.3) else 0
    stage_7d = 0
    if pd.notna(peak_7d):
        ratio = peak_7d / preop_cr
        rose_meaningfully = (peak_7d - preop_cr) >= 0.3
        if ratio >= 3.0 or (peak_7d >= 4.0 and rose_meaningfully):
            stage_7d = 3
        elif ratio >= 2.0:
            stage_7d = 2
        elif ratio >= 1.5:
            stage_7d = 1
    return max(stage_48h, stage_7d)


def main():
    feats = pd.read_parquet(DATA_DIR / "temperature_features_partial.parquet")
    candidate = pd.read_parquet(DATA_DIR / "candidate_cohort.parquet")
    clin = pd.read_csv(RAW_DIR / "clinical_data.csv")
    lab = pd.read_csv(RAW_DIR / "lab_data.csv")

    # candidate_cohort.parquet already carries opend/preop_cr from 01_extract_cohort.py
    # (it kept all clinical_data.csv columns), so no need to re-merge those.
    cohort = candidate.merge(feats[["caseid", "status", "bt_coverage_trimmed"]], on="caseid", how="left")
    cohort["included"] = (cohort["status"] == "ok") & (cohort["bt_coverage_trimmed"] >= 0.95)

    cohort["peak_cr_48h"] = get_lab_value(cohort, lab, "cr", "opend", 0, 48 * HOUR, agg="max")
    cohort["peak_cr_7d"] = get_lab_value(cohort, lab, "cr", "opend", 0, 7 * DAY, agg="max")
    cohort["aki_stage"] = [
        stage_kdigo(pc, p48, p7d)
        for pc, p48, p7d in zip(cohort["preop_cr"], cohort["peak_cr_48h"], cohort["peak_cr_7d"])
    ]
    cohort["aki_any"] = cohort["aki_stage"] >= 1

    for name in ["ptinr", "aptt", "fib"]:
        preop = get_lab_value(cohort, lab, name, "opend", -PREOP_LOOKBACK_SEC, 0, agg="last")
        postop = get_lab_value(cohort, lab, name, "opend", 0, 24 * HOUR, agg="first")
        cohort[f"delta_{name}"] = postop - preop

    print(f"Full candidate cohort with outcomes computed: N={len(cohort)} "
          f"(included={cohort['included'].sum()}, excluded={(~cohort['included']).sum()})")
    print()

    tbl = pd.read_csv(TABLES_DIR / "excluded_vs_included_comparison.csv")
    rows = []

    def add_cont(label, col):
        inc = cohort.loc[cohort["included"], col].dropna()
        exc = cohort.loc[~cohort["included"], col].dropna()
        _, p = stats.ttest_ind(inc, exc, equal_var=False)
        rows.append([label, f"{inc.mean():.2f} +/- {inc.std():.2f} (n={len(inc)})",
                     f"{exc.mean():.2f} +/- {exc.std():.2f} (n={len(exc)})", f"{p:.4f}"])

    def add_cat(label, col, val):
        inc_mask = cohort.loc[cohort["included"], col] == val
        exc_mask = cohort.loc[~cohort["included"], col] == val
        inc_n = cohort.loc[cohort["included"], col].notna().sum()
        exc_n = cohort.loc[~cohort["included"], col].notna().sum()
        tab = pd.crosstab(cohort["included"], cohort[col] == val)
        _, p, _, _ = stats.chi2_contingency(tab)
        rows.append([label, f"{inc_mask.mean():.1%} (n={inc_n})", f"{exc_mask.mean():.1%} (n={exc_n})", f"{p:.4f}"])

    add_cat("Any AKI (stage>=1)", "aki_any", True)
    add_cont("Delta PT-INR", "delta_ptinr")
    add_cont("Delta aPTT, sec", "delta_aptt")
    add_cont("Delta fibrinogen, mg/dL", "delta_fib")

    ext = pd.DataFrame(rows, columns=tbl.columns)
    full = pd.concat([tbl, ext], ignore_index=True)
    print(full.to_string(index=False))
    full.to_csv(TABLES_DIR / "excluded_vs_included_comparison.csv", index=False)
    print(f"\nUpdated -> {TABLES_DIR / 'excluded_vs_included_comparison.csv'}")


if __name__ == "__main__":
    main()
