"""
Direct comparison: does v1's Delta-Hb finding replicate under the exact same
rigor (covariates, cohort, model type) as the new EBL-based Aim 1 model?
Locked as SS6d.

The ONLY intended difference between the two models is the outcome variable.
One necessary deviation, flagged rather than silently applied: log_ebl uses
log1p (EBL is right-skewed and >=0); delta_hb can be negative (Hb can rise
postop), so it is modeled untransformed -- matching how v1 itself modeled it.
Everything else (covariates, cohort N=2,567, OLS) is identical.

Do not assume the result. Report whichever way it comes out.
"""
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
TABLES_DIR = PROJECT_DIR / "outputs" / "tables"

COVARIATES = ["age", "male", "bmi", "C(asa)", "emop", "C(optype)", "opdur_min",
              "intraop_crystalloid", "intraop_colloid", "vasopressor_use"]
COV_STR = " + ".join(COVARIATES)


def main():
    df = pd.read_parquet(DATA_DIR / "analysis_primary_data.parquet")
    print(f"N (full Aim 1 cohort) = {len(df)}")
    print()

    f_ebl = f"log_ebl ~ hypothermia_burden + min_core_temp + {COV_STR}"
    f_hb = f"delta_hb ~ hypothermia_burden + min_core_temp + {COV_STR}"

    m_ebl = smf.ols(f_ebl, data=df).fit()
    m_hb = smf.ols(f_hb, data=df).fit()

    print(f"EBL model N = {int(m_ebl.nobs)} (outcome: log1p(intraop_ebl))")
    print(f"Delta-Hb model N = {int(m_hb.nobs)} (outcome: preop_hb - postop_hb, untransformed; "
          f"{df['delta_hb'].notna().sum()}/{len(df)} = {df['delta_hb'].notna().mean():.1%} complete)")
    print()

    rows = []
    for label, m in [("log(EBL+1)", m_ebl), ("Delta Hb (untransformed)", m_hb)]:
        term = "hypothermia_burden"
        coef, se, p = m.params[term], m.bse[term], m.pvalues[term]
        ci = m.conf_int().loc[term]
        rows.append([label, int(m.nobs), coef, se, ci[0], ci[1], p, m.rsquared])
        print(f"--- {label} (N={int(m.nobs)}, R2={m.rsquared:.4f}) ---")
        print(f"  burden: beta={coef:.6f}, SE={se:.6f}, 95% CI [{ci[0]:.6f}, {ci[1]:.6f}], p={p:.4f}")
        print(f"  {'SIGNIFICANT' if p < 0.05 else 'not significant'} at alpha=0.05")
        print()

    tbl = pd.DataFrame(rows, columns=["Outcome", "N", "Beta (burden)", "SE", "CI_low", "CI_high", "p-value", "R2"])
    print("=" * 70)
    print("TABLE 9: v1 (Delta Hb) vs. v2 (EBL) -- same covariates, same cohort, same model type")
    print("=" * 70)
    print(tbl.to_string(index=False))

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    tbl.to_csv(TABLES_DIR / "table9_v1_replication_comparison.csv", index=False)
    print(f"\nSaved -> {TABLES_DIR / 'table9_v1_replication_comparison.csv'}")

    print()
    print("=== Verdict (not assumed) ===")
    p_hb = m_hb.pvalues["hypothermia_burden"]
    p_ebl = m_ebl.pvalues["hypothermia_burden"]
    if p_hb < 0.05:
        print(f"Burden IS significant for Delta Hb (p={p_hb:.4f}) under the same covariates/cohort as the EBL model.")
        print(f"EBL model: p={p_ebl:.4f} ({'significant' if p_ebl < 0.05 else 'not significant'}).")
        print("v1's finding DOES replicate on its own outcome scale, even though it doesn't transfer to")
        print("directly-measured EBL -- the two outcomes are telling different stories, not just noisier/cleaner")
        print("versions of the same one.")
    else:
        print(f"Burden is NOT significant for Delta Hb either (p={p_hb:.4f}), matching the EBL result (p={p_ebl:.4f}).")
        print("v1's original finding does not replicate even on its own outcome scale once the fuller,")
        print("more carefully specified covariate adjustment used throughout this pipeline is applied.")


if __name__ == "__main__":
    main()
