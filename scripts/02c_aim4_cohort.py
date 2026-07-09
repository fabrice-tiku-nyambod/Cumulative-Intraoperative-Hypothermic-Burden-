"""
Backfills mbp_coverage_trimmed into the cached temperature_features_partial.parquet
(computed locally from the already-cached mbp_raw arrays -- no vitaldb.load_case()
calls needed) and writes the confirmed Aim 4 cohort: analytic cohort (BT trimmed
>=95%) AND MAP trimmed >=95%, i.e. the arterial-line subset.

Run once after 02_build_exposures.py has produced a full cache. A fresh full run
of 02_build_exposures.py now computes mbp_coverage_trimmed natively, making this
script unnecessary going forward -- it exists to backfill the one cache that
predates that field.
"""
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"

COVERAGE_MIN_TRIMMED = 0.95
MBP_COVERAGE_MIN_TRIMMED = 0.95


def trimmed_coverage(raw):
    arr = np.array(raw, dtype=float)
    valid = ~np.isnan(arr)
    if valid.sum() == 0:
        return 0.0
    idx = np.flatnonzero(valid)
    first, last = idx[0], idx[-1]
    trimmed = valid[first:last + 1]
    return trimmed.sum() / len(trimmed)


def main():
    df = pd.read_parquet(DATA_DIR / "temperature_features_partial.parquet")
    ok = df[df["status"] == "ok"].copy()

    if "mbp_coverage_trimmed" not in ok.columns or ok["mbp_coverage_trimmed"].isna().all():
        ok["mbp_coverage_trimmed"] = ok["mbp_raw"].apply(trimmed_coverage)
        df.loc[ok.index, "mbp_coverage_trimmed"] = ok["mbp_coverage_trimmed"]
        df.to_parquet(DATA_DIR / "temperature_features_partial.parquet", index=False)
        print("Backfilled mbp_coverage_trimmed into temperature_features_partial.parquet")
    else:
        print("mbp_coverage_trimmed already present, skipping backfill")

    final = ok[ok["bt_coverage_trimmed"] >= COVERAGE_MIN_TRIMMED]
    final.to_parquet(DATA_DIR / "final_exposure_cohort.parquet", index=False)
    print(f"Final analytic cohort (BT trimmed >= {COVERAGE_MIN_TRIMMED:.0%}): N = {len(final)}")

    aim4 = final[final["mbp_coverage_trimmed"] >= MBP_COVERAGE_MIN_TRIMMED]
    aim4.to_parquet(DATA_DIR / "aim4_cohort.parquet", index=False)
    print(f"Aim 4 cohort (analytic AND MAP trimmed >= {MBP_COVERAGE_MIN_TRIMMED:.0%}, a-line subset): "
          f"N = {len(aim4)} ({len(aim4)/len(final):.1%} of analytic cohort)")
    print(f"-> {DATA_DIR / 'aim4_cohort.parquet'}")


if __name__ == "__main__":
    main()
