"""
Stage 1 of 2 in the cohort lock (see protocol SS9).

Fast, deterministic, network-free filtering directly off clinical_data.csv:
age, department, operative duration, reoperation dedup. Deliberately does
NOT apply the intraop_ebl/transfusion-field completeness exclusion or the
BT/ART_MBP >=80% coverage exclusion -- both wait for 02_build_exposures.py,
which streams the same tracks anyway and can apply coverage-based exclusion
in that same pass rather than paying for it twice.

Output of this script is the CANDIDATE cohort, not the final analytic
cohort. Table 1 / STROBE diagram must cite 02's output N, not this one.
"""
import pandas as pd
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR.parent / "DATASET"
OUT_DIR = PROJECT_DIR / "data"

TARGET_DEPARTMENTS = ["General surgery", "Thoracic surgery", "Gynecology", "Urology"]
MIN_AGE = 18
MIN_OPDUR_MIN = 120


def attrition_step(log, label, df_before, df_after, note=""):
    log.append({
        "step": label,
        "n_before": len(df_before),
        "n_excluded": len(df_before) - len(df_after),
        "n_after": len(df_after),
        "note": note,
    })
    return log


def main():
    clin = pd.read_csv(DATA_DIR / "clinical_data.csv")
    clin["age"] = pd.to_numeric(clin["age"], errors="coerce")
    clin["opdur_min"] = (clin["opend"] - clin["opstart"]) / 60.0

    log = []
    df = clin
    log = attrition_step(log, "Total cases in clinical_data.csv", df, df)

    step = df[df["department"].isin(TARGET_DEPARTMENTS)]
    log = attrition_step(log, "Department in {General surgery, Thoracic surgery, Gynecology, Urology}", df, step)
    df = step

    step = df[df["age"] >= MIN_AGE]
    log = attrition_step(log, f"Age >= {MIN_AGE}", df, step, note=f"{df['age'].isna().sum()} cases had unparseable/missing age")
    df = step

    step = df[df["opdur_min"] > MIN_OPDUR_MIN]
    log = attrition_step(log, f"Operative duration (opend-opstart) > {MIN_OPDUR_MIN} min", df, step)
    df = step

    dup_counts = df["subjectid"].value_counts()
    reoperated_subjects = dup_counts[dup_counts > 1].index
    step = df.sort_values("opstart").drop_duplicates(subset="subjectid", keep="first")
    log = attrition_step(
        log, "Reoperation dedup (keep index case per subjectid)", df, step,
        note=f"{len(reoperated_subjects)} subjects had >1 case; kept earliest opstart per subject",
    )
    df = step

    df = df.sort_values("caseid").reset_index(drop=True)

    attrition_df = pd.DataFrame(log)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    attrition_df.to_csv(OUT_DIR / "attrition_log_01_candidate_cohort.csv", index=False)
    df.to_parquet(OUT_DIR / "candidate_cohort.parquet", index=False)

    print(attrition_df.to_string(index=False))
    print()
    print(f"Candidate cohort N = {len(df)} -> {OUT_DIR / 'candidate_cohort.parquet'}")
    print("NOTE: this is the candidate cohort, not the final analytic cohort.")
    print("02_build_exposures.py applies the BT/ART_MBP >=80% coverage exclusion")
    print("and outcome-completeness exclusions on top of this set.")


if __name__ == "__main__":
    main()
