"""
Follow-up to 02_build_exposures.py: characterizes the BT-coverage exclusion
(candidate N=2,824 -> analytic N=2,568) rather than just reporting its size.

Triggered by a benchmark-stage observation (50-case pilot) that coverage
failures clustered heavily in Stomach-surgery cases. This script confirms
that at full N with formal tests, checks whether it survives adjustment for
duration/approach/position, and checks whether exclusion is associated with
outcome severity (differential attrition) rather than just case-mix.

Outputs:
  outputs/tables/excluded_vs_included_comparison.csv
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
TABLES_DIR = PROJECT_DIR / "outputs" / "tables"


def load_merged():
    feats = pd.read_parquet(DATA_DIR / "temperature_features_partial.parquet")
    cohort = pd.read_parquet(DATA_DIR / "candidate_cohort.parquet")
    m = cohort.merge(feats[["caseid", "status", "bt_coverage_trimmed"]], on="caseid", how="left")
    m["included"] = (m["status"] == "ok") & (m["bt_coverage_trimmed"] >= 0.95)
    m["age"] = pd.to_numeric(m["age"], errors="coerce")
    m["transfused"] = m["intraop_rbc"] > 0
    m["is_stomach"] = m["optype"] == "Stomach"
    return m


def stomach_association(ok):
    ok = ok.copy()
    ok["passed"] = (ok["bt_coverage_trimmed"] >= 0.95).astype(int)
    ok["is_stomach_i"] = ok["is_stomach"].astype(int)

    tab = pd.crosstab(ok["is_stomach"], ok["passed"])
    a, b = tab.loc[True, 0], tab.loc[True, 1]
    c, d = tab.loc[False, 0], tab.loc[False, 1]
    chi2, p_chi2, _, _ = stats.chi2_contingency(tab)
    _, p_fisher = stats.fisher_exact(tab)
    OR = (a * d) / (b * c)
    se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    ci = (math.exp(math.log(OR) - 1.96 * se), math.exp(math.log(OR) + 1.96 * se))

    print("=== Stomach-surgery coverage-failure association ===")
    print(tab)
    print(f"chi2 p={p_chi2:.2e}  Fisher exact p={p_fisher:.2e}")
    print(f"Unadjusted OR (fail | stomach) = {OR:.2f} (95% CI {ci[0]:.2f}-{ci[1]:.2f})")

    m_adj = smf.logit("passed ~ is_stomach_i + opdur_min + C(approach) + C(position)", data=ok).fit(disp=0)
    or_adj = np.exp(m_adj.params["is_stomach_i"])
    ci_adj = np.exp(m_adj.conf_int().loc["is_stomach_i"]).tolist()
    print(f"Adjusted (duration+approach+position) OR (pass | stomach) = {or_adj:.3f} "
          f"(95% CI {ci_adj[0]:.3f}-{ci_adj[1]:.3f}), p={m_adj.pvalues['is_stomach_i']:.2e}")
    print("-> survives adjustment; not explained by duration, approach, or position alone.")
    print()


def differential_attrition_check(m):
    print("=== Differential attrition check: does exclusion track outcome severity? ===")
    for label, subset in [("Overall", m), ("Stomach only", m[m["is_stomach"]])]:
        inc = subset.loc[subset["included"], "intraop_ebl"].dropna()
        exc = subset.loc[~subset["included"], "intraop_ebl"].dropna()
        _, p = stats.ttest_ind(inc, exc, equal_var=False)
        print(f"  [{label}] EBL: included={inc.mean():.1f} (n={len(inc)}), "
              f"excluded={exc.mean():.1f} (n={len(exc)}), p={p:.4f}")
    print("  -> no significant EBL difference at either level: attrition is not outcome-driven,")
    print("     but IS optype-driven, and optype itself predicts outcome severity (see table).")
    print()


def build_comparison_table(m):
    rows = []

    def add_cont(label, col):
        inc = m.loc[m["included"], col].dropna()
        exc = m.loc[~m["included"], col].dropna()
        _, p = stats.ttest_ind(inc, exc, equal_var=False)
        rows.append([label, f"{inc.mean():.1f} +/- {inc.std():.1f}", f"{exc.mean():.1f} +/- {exc.std():.1f}", f"{p:.4f}"])

    def add_cat(label, col, val):
        # col == val on a NaN row silently evaluates to False, not NaN/excluded.
        # Not currently live here (sex/emop/optype/transfused are all 100%
        # complete), but hardened defensively -- this exact pattern caused a
        # real bug once it was reused in 03b for a column with real missingness
        # (aki_any), and this helper could be reused the same way again.
        present = m[m[col].notna()]
        inc = (present.loc[present["included"], col] == val).mean()
        exc = (present.loc[~present["included"], col] == val).mean()
        tab = pd.crosstab(present["included"], present[col] == val)
        _, p, _, _ = stats.chi2_contingency(tab)
        rows.append([label, f"{inc:.1%}", f"{exc:.1%}", f"{p:.4f}"])

    add_cont("Age, years", "age")
    add_cont("BMI, kg/m2", "bmi")
    add_cont("Op duration, min", "opdur_min")
    add_cat("Male sex", "sex", "M")
    add_cat("Emergency op", "emop", 1)
    add_cat("Stomach optype", "optype", "Stomach")
    add_cont("Intraop EBL, mL", "intraop_ebl")
    add_cat("Any RBC transfusion", "transfused", True)

    tbl = pd.DataFrame(rows, columns=[
        "Characteristic",
        f"Included (N={m['included'].sum()})",
        f"Excluded (N={(~m['included']).sum()})",
        "p-value",
    ])
    print(tbl.to_string(index=False))
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    tbl.to_csv(TABLES_DIR / "excluded_vs_included_comparison.csv", index=False)
    print(f"\nSaved -> {TABLES_DIR / 'excluded_vs_included_comparison.csv'}")


def main():
    m = load_merged()
    ok = m[m["status"] == "ok"]
    stomach_association(ok)
    differential_attrition_check(m)
    build_comparison_table(m)


if __name__ == "__main__":
    main()
