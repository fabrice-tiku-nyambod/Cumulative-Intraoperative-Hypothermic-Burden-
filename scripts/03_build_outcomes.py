"""
Stage 3: builds outcome variables for the final analytic cohort (N=2,568),
per protocol SS6 and the decisions locked in SS3b item 4.

All local file joins against clinical_data.csv / lab_data.csv -- no live API
calls, so none of 02's benchmark/checkpoint/retry machinery is needed here.

Anchor for every postoperative window: opend (surgical end), consistent
with the LOS anchor already locked ("surgical end is the conventional
clinical anchor... anesthesia-emergence timing is noisier").

Baseline conventions:
  - preop_cr, preop_hb: taken directly from clinical_data.csv's own
    pre-summarized columns (per explicit instruction for cr; hb follows
    the same existing convention used throughout this pipeline).
  - preop ptinr/aptt/fib: clinical_data.csv only has preop_pt/preop_aptt as
    single pre-summarized values of UNCONFIRMED unit/scale relative to
    lab_data.csv's ptinr/ptsec/pt%/aptt names, and has no preop_fib at all.
    SS6 phrasing ("last preoperative value to first postoperative value")
    implies both ends should come from the same source with guaranteed-
    matching units -- so all three are derived from lab_data.csv directly
    (last value in the 90 days before opend), not from clinical_data.csv.
    Flagging this as an interpretive call, not a silent assumption.

KDIGO AKI staging: 48h absolute-delta and 7d ratio criteria evaluated
independently against peak (max) creatinine in each window, max stage wins.
"""
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = PROJECT_DIR.parent / "DATASET"

DAY = 86400
HOUR = 3600
PREOP_LOOKBACK_SEC = 90 * DAY


def get_lab_value(cohort, lab, lab_name, anchor_col, window_start_sec, window_end_sec, agg="first"):
    """Reusable lab-lookup (per SS6): pulls `lab_name` values from `lab`
    (long-format lab_data.csv) falling within [window_start_sec, window_end_sec]
    relative to each case's anchor_col, aggregated per case by `agg`:
      "first" -> earliest qualifying value (for postop windows)
      "last"  -> latest qualifying value (for "last preoperative value")
      "max"   -> peak value in window (for KDIGO staging)
    Returns an array aligned to cohort's row order (NaN where no qualifying
    value exists)."""
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
    """KDIGO creatinine-only staging. 48h absolute-delta criterion stages
    only Stage 1 (per KDIGO definition); 7d ratio criterion stages 1-3.
    Max of the two wins. NaN if baseline or both windows are missing.

    The literal KDIGO Stage 3 "SCr >=4.0 mg/dl" criterion is conditioned
    here on an accompanying rise of >=0.3 mg/dl from baseline (same
    threshold as the 48h Stage 1 criterion). Without this, patients with
    chronic elevated baseline creatinine (dialysis/ESRD) whose creatinine
    never actually rises get misclassified as Stage 3 AKI purely for being
    chronically at a high absolute level -- confirmed empirically: 90/103
    Stage-3-via-absolute-criterion cases had a mean ratio of 0.97 (i.e. no
    real change from baseline)."""
    if pd.isna(preop_cr) or (pd.isna(peak_48h) and pd.isna(peak_7d)):
        return np.nan

    stage_48h = 0
    if pd.notna(peak_48h) and (peak_48h - preop_cr) >= 0.3:
        stage_48h = 1

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
    cohort = pd.read_parquet(DATA_DIR / "final_exposure_cohort.parquet")[["caseid"]].copy()
    clin = pd.read_csv(RAW_DIR / "clinical_data.csv")
    lab = pd.read_csv(RAW_DIR / "lab_data.csv")

    cohort = cohort.merge(
        clin[["caseid", "opend", "dis", "icu_days", "death_inhosp",
              "preop_cr", "preop_hb", "intraop_ebl", "intraop_rbc", "intraop_ffp"]],
        on="caseid", how="left",
    )
    assert len(cohort) == 2568, f"expected 2568 rows, got {len(cohort)}"
    assert cohort["caseid"].is_unique, "duplicate caseid after merge"
    assert cohort["opend"].notna().all(), "opend missing for some cases -- anchor cannot be null"

    # --- Aim 1: blood loss and transfusion, direct from clinical_data.csv ---
    cohort["transfused"] = cohort["intraop_rbc"] > 0

    # --- Aim 2: coagulation derangement, delta from last preop to first postop-24h value ---
    for name in ["ptinr", "aptt", "fib"]:
        preop = get_lab_value(cohort, lab, name, "opend", -PREOP_LOOKBACK_SEC, 0, agg="last")
        postop = get_lab_value(cohort, lab, name, "opend", 0, 24 * HOUR, agg="first")
        cohort[f"preop_{name}_lab"] = preop
        cohort[f"postop_{name}"] = postop
        cohort[f"delta_{name}"] = postop - preop

    # --- Aim 2 sensitivity outcome: delta Hb (preop from clinical_data.csv, postop first-24h from lab_data.csv) ---
    cohort["postop_hb"] = get_lab_value(cohort, lab, "hb", "opend", 0, 24 * HOUR, agg="first")
    cohort["delta_hb"] = cohort["preop_hb"] - cohort["postop_hb"]

    # --- Aim 3: AKI (KDIGO), peak creatinine in 48h and 7d windows from opend, preop_cr from clinical_data.csv ---
    cohort["peak_cr_48h"] = get_lab_value(cohort, lab, "cr", "opend", 0, 48 * HOUR, agg="max")
    cohort["peak_cr_7d"] = get_lab_value(cohort, lab, "cr", "opend", 0, 7 * DAY, agg="max")
    cohort["aki_stage"] = [
        stage_kdigo(pc, p48, p7d)
        for pc, p48, p7d in zip(cohort["preop_cr"], cohort["peak_cr_48h"], cohort["peak_cr_7d"])
    ]
    cohort["aki_any"] = cohort["aki_stage"] >= 1

    # --- Aim 3: LOS and mortality, direct from clinical_data.csv ---
    cohort["los_postop_days"] = (cohort["dis"] - cohort["opend"]) / DAY
    n_negative_los = (cohort["los_postop_days"] < 0).sum()
    if n_negative_los:
        print(f"WARNING: {n_negative_los} case(s) have dis < opend (discharge recorded before "
              f"surgery end) -- raw-data anomaly in clinical_data.csv, not a pipeline bug. "
              f"Nulling los_postop_days for: {cohort.loc[cohort['los_postop_days'] < 0, 'caseid'].tolist()}")
        cohort.loc[cohort["los_postop_days"] < 0, "los_postop_days"] = np.nan

    cohort.to_parquet(DATA_DIR / "outcomes.parquet", index=False)

    print(f"outcomes.parquet written: {len(cohort)} rows, {cohort.shape[1]} columns")
    print(f"-> {DATA_DIR / 'outcomes.parquet'}")
    print()
    print("=== Completeness ===")
    for col in ["intraop_ebl", "transfused", "delta_ptinr", "delta_aptt", "delta_fib",
                "delta_hb", "aki_stage", "los_postop_days", "icu_days", "death_inhosp"]:
        print(f"  {col}: {cohort[col].notna().sum()}/{len(cohort)} ({cohort[col].notna().mean():.1%})")
    print()
    print("=== AKI stage distribution ===")
    print(cohort["aki_stage"].value_counts(dropna=False).sort_index())
    print()
    print("=== Quick ranges (sanity) ===")
    print(cohort[["los_postop_days", "delta_hb", "delta_ptinr", "delta_aptt", "delta_fib"]].describe())


if __name__ == "__main__":
    main()
