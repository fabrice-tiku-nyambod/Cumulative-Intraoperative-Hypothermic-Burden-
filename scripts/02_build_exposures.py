"""
Stage 2 of 2 in the cohort lock (see protocol SS9 / SS4 / SS5).

Streams Solar8000/BT and Solar8000/ART_MBP for each candidate case via
vitaldb.load_case(), applies the coverage exclusion in the same pass (per
the two-stage split agreed with the user -- no point streaming twice), and
computes the primary/comparator exposure metrics.

Coverage rule (locked, per S4): trim each case to its own OBSERVED monitored
window -- [first valid BT reading, last valid BT reading] within the
anesthesia window -- rather than a fixed global buffer, then require >=95%
coverage within that trimmed window. Benchmark showed near-zero interior
dropout once probe placement/removal edges are excluded, so 95% on the
trimmed window is a real bar, not a loosened one. bt_coverage_full_window
(coverage over the untrimmed [anestart, aneend] span) is also reported for
transparency/comparison but does NOT gate inclusion.

Burden itself is still integrated over the full anesthesia window
regardless of the trim -- the trim only affects the inclusion metric.

Resumable: each successful case is appended to a checkpoint file and a
partial-results parquet immediately, so a network failure mid-run only
costs the in-flight case, not the whole pass.

Usage:
    python 02_build_exposures.py --limit 50      # benchmark on first 50
    python 02_build_exposures.py                 # full candidate cohort
"""
import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd
import vitaldb

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"

INTERVAL_SEC = 10
BT_ARTIFACT_LOW, BT_ARTIFACT_HIGH = 32.0, 41.0
HYPOTHERMIA_THRESHOLD = 36.0
MAP_HYPOTENSION_THRESHOLD = 65.0
COVERAGE_MIN_TRIMMED = 0.95
MBP_COVERAGE_MIN_TRIMMED = 0.95  # Aim 4 (a-line subset) inclusion rule, same threshold as BT
EARLY_WINDOW_MIN = 30

CHECKPOINT_PATH = DATA_DIR / "checkpoint_completed_caseids.txt"
PARTIAL_PATH = DATA_DIR / "temperature_features_partial.parquet"
FLUSH_EVERY = 25


def load_checkpoint():
    if CHECKPOINT_PATH.exists():
        done = set(int(x) for x in CHECKPOINT_PATH.read_text().split())
    else:
        done = set()
    if PARTIAL_PATH.exists():
        prior = pd.read_parquet(PARTIAL_PATH).to_dict("records")
    else:
        prior = []
    return done, prior


def append_checkpoint(caseid):
    with open(CHECKPOINT_PATH, "a") as f:
        f.write(f"{caseid}\n")


def extract_case_features(caseid, anestart, aneend):
    tracks = vitaldb.load_case(caseid, ["Solar8000/BT", "Solar8000/ART_MBP"], INTERVAL_SEC)
    if tracks is None or len(tracks) == 0:
        return {"caseid": caseid, "status": "no_track_data"}

    bt = tracks[:, 0]
    mbp = tracks[:, 1]
    t_sec = np.arange(len(bt)) * INTERVAL_SEC
    dt_min = INTERVAL_SEC / 60.0

    win = (t_sec >= max(anestart, 0)) & (t_sec <= aneend)
    expected_n = int(win.sum())
    if expected_n == 0:
        return {"caseid": caseid, "status": "empty_anesthesia_window"}

    bt_w, mbp_w, t_w = bt[win], mbp[win], t_sec[win]

    bt_ok = ~np.isnan(bt_w) & (bt_w >= BT_ARTIFACT_LOW) & (bt_w <= BT_ARTIFACT_HIGH)
    bt_valid = bt_w[bt_ok]
    bt_coverage_full_window = bt_ok.sum() / expected_n

    if bt_ok.sum() == 0:
        return {
            "caseid": caseid, "status": "no_valid_bt",
            "bt_coverage_full_window": 0.0, "bt_coverage_trimmed": 0.0,
            "bt_time_sec": t_w.tolist(), "bt_raw": bt_w.tolist(), "mbp_raw": mbp_w.tolist(),
        }

    # Per-case observed monitored window: first valid reading -> last valid reading.
    valid_idx = np.flatnonzero(bt_ok)
    first_idx, last_idx = valid_idx[0], valid_idx[-1]
    trimmed_n = last_idx - first_idx + 1
    trimmed_ok = bt_ok[first_idx:last_idx + 1]
    bt_coverage_trimmed = trimmed_ok.sum() / trimmed_n
    interior_missing_count = int((~trimmed_ok).sum())
    pre_monitoring_gap_sec = float(t_w[first_idx] - t_w[0])
    post_monitoring_gap_sec = float(t_w[-1] - t_w[last_idx])
    trimmed_window_start_sec = float(t_w[first_idx])
    trimmed_window_end_sec = float(t_w[last_idx])

    burden = np.sum(np.maximum(0.0, HYPOTHERMIA_THRESHOLD - bt_valid) * dt_min)
    hypothermia_duration_min = np.sum(bt_valid < HYPOTHERMIA_THRESHOLD) * dt_min
    min_core_temp = float(np.min(bt_valid))

    # 2-min median-smoothed nadir (12 samples at 10s interval), NaN/artifact-masked first
    bt_masked = np.where(bt_ok, bt_w, np.nan)
    smoothed = pd.Series(bt_masked).rolling(window=12, min_periods=6, center=True).median()
    min_core_temp_smoothed = float(np.nanmin(smoothed)) if smoothed.notna().any() else np.nan

    # Early thermal drop velocity: steepest decline in the first 30 min of the anesthesia window
    early_mask = bt_ok & (t_w <= t_w[0] + EARLY_WINDOW_MIN * 60)
    if early_mask.sum() >= 2:
        t0_temp = bt_w[early_mask][0]
        early_min = np.min(bt_w[early_mask])
        early_thermal_drop_velocity = max(0.0, (t0_temp - early_min)) / EARLY_WINDOW_MIN
    else:
        early_thermal_drop_velocity = np.nan

    mbp_ok = ~np.isnan(mbp_w)
    mbp_coverage = mbp_ok.sum() / expected_n
    mbp_valid = mbp_w[mbp_ok]
    hypotension_burden = (
        np.sum(np.maximum(0.0, MAP_HYPOTENSION_THRESHOLD - mbp_valid) * dt_min)
        if mbp_ok.sum() > 0
        else np.nan
    )

    # Aim 4 (a-line subset only): same trimmed-window >=95% rule as BT, applied
    # to MAP. Cases with zero MAP data (no arterial line) get trimmed coverage
    # 0.0, which correctly fails the threshold rather than raising.
    if mbp_ok.sum() > 0:
        mbp_valid_idx = np.flatnonzero(mbp_ok)
        mbp_first, mbp_last = mbp_valid_idx[0], mbp_valid_idx[-1]
        mbp_trimmed_ok = mbp_ok[mbp_first:mbp_last + 1]
        mbp_coverage_trimmed = mbp_trimmed_ok.sum() / len(mbp_trimmed_ok)
    else:
        mbp_coverage_trimmed = 0.0

    return {
        "caseid": caseid,
        "status": "ok",
        "bt_coverage_full_window": bt_coverage_full_window,
        "bt_coverage_trimmed": bt_coverage_trimmed,
        "mbp_coverage": mbp_coverage,
        "mbp_coverage_trimmed": mbp_coverage_trimmed,
        "hypothermia_burden": burden,
        "hypothermia_duration_min": hypothermia_duration_min,
        "min_core_temp": min_core_temp,
        "min_core_temp_smoothed": min_core_temp_smoothed,
        "early_thermal_drop_velocity": early_thermal_drop_velocity,
        "hypotension_burden": hypotension_burden,
        # Gap-structure summary, so future rule changes (coverage definition,
        # burden formula, artifact bounds) are a recompute against the raw
        # arrays below, not a re-pull from the API.
        "interior_missing_count": interior_missing_count,
        "pre_monitoring_gap_sec": pre_monitoring_gap_sec,
        "post_monitoring_gap_sec": post_monitoring_gap_sec,
        "trimmed_window_start_sec": trimmed_window_start_sec,
        "trimmed_window_end_sec": trimmed_window_end_sec,
        "anestart": float(anestart),
        "aneend": float(aneend),
        # Raw per-case arrays (full anesthesia window, pre-artifact-filter).
        # Anything downstream is derivable from these three without touching
        # vitaldb.load_case() again.
        "bt_time_sec": t_w.tolist(),
        "bt_raw": bt_w.tolist(),
        "mbp_raw": mbp_w.tolist(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="Process only the first N candidate cases (benchmark mode)")
    args = ap.parse_args()

    cohort = pd.read_parquet(DATA_DIR / "candidate_cohort.parquet")
    if args.limit:
        cohort = cohort.head(args.limit)

    done, results = load_checkpoint()
    todo = cohort[~cohort["caseid"].isin(done)]
    print(f"Candidate cases: {len(cohort)} | already checkpointed: {len(done & set(cohort['caseid']))} | to process: {len(todo)}")

    t_start = time.time()
    n_processed = 0
    for _, row in todo.iterrows():
        t0 = time.time()
        try:
            feat = extract_case_features(row["caseid"], row["anestart"], row["aneend"])
        except Exception as e:
            feat = {"caseid": row["caseid"], "status": f"error: {e}"}
        feat["fetch_seconds"] = round(time.time() - t0, 3)
        results.append(feat)
        append_checkpoint(row["caseid"])
        n_processed += 1

        if n_processed % FLUSH_EVERY == 0:
            pd.DataFrame(results).to_parquet(PARTIAL_PATH, index=False)
            elapsed = time.time() - t_start
            rate = n_processed / elapsed
            print(f"  ...{n_processed}/{len(todo)} done, {rate:.2f} cases/sec, ETA {(len(todo)-n_processed)/rate/60:.1f} min")

    df = pd.DataFrame(results)
    df.to_parquet(PARTIAL_PATH, index=False)

    print()
    print(f"Total processed this run: {n_processed} in {time.time()-t_start:.1f}s")
    print()
    print("Status breakdown:")
    print(df["status"].value_counts())
    ok = df[df["status"] == "ok"]
    if len(ok):
        print()
        print("Coverage rule comparison (transparency only -- inclusion is gated by the trimmed/95% rule):")
        print(f"  Full-window >= 80%  (rejected rule): {(ok['bt_coverage_full_window'] >= 0.80).sum()} / {len(ok)}")
        print(f"  Trimmed >= {COVERAGE_MIN_TRIMMED:.0%}   (locked rule):    {(ok['bt_coverage_trimmed'] >= COVERAGE_MIN_TRIMMED).sum()} / {len(ok)}")
        print()
        print(ok[["bt_coverage_full_window", "bt_coverage_trimmed", "mbp_coverage", "hypothermia_burden", "min_core_temp", "hypothermia_duration_min"]].describe())

    if not args.limit:
        final = df[(df["status"] == "ok") & (df["bt_coverage_trimmed"] >= COVERAGE_MIN_TRIMMED)]
        final.to_parquet(DATA_DIR / "final_exposure_cohort.parquet", index=False)
        print()
        print(f"Final analytic cohort (candidate AND trimmed BT coverage >= {COVERAGE_MIN_TRIMMED:.0%}): N = {len(final)}")
        print(f"-> {DATA_DIR / 'final_exposure_cohort.parquet'}")

        # Aim 4 cohort: analytic cohort AND MAP trimmed coverage >= 95% (a-line subset only).
        aim4 = final[final["mbp_coverage_trimmed"] >= MBP_COVERAGE_MIN_TRIMMED]
        aim4.to_parquet(DATA_DIR / "aim4_cohort.parquet", index=False)
        print(f"Aim 4 cohort (analytic cohort AND trimmed MAP coverage >= {MBP_COVERAGE_MIN_TRIMMED:.0%}, "
              f"i.e. arterial-line subset): N = {len(aim4)} ({len(aim4)/len(final):.1%} of analytic cohort)")
        print(f"-> {DATA_DIR / 'aim4_cohort.parquet'}")


if __name__ == "__main__":
    main()
