"""
Aims 2-3 secondary analysis: AKI, LOS, ICU admission (confirmatory-ish,
Holm-Bonferroni scoped to AKI+LOS per locked decision), coagulation
(exploratory, no correction), mortality (descriptive only, 17 events).

Loads analysis_primary_data.parquet directly (same N=2,567 cohort, same
covariates/exposures/optype_collapsed already built in 04) rather than
rebuilding from scratch.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
TABLES_DIR = PROJECT_DIR / "outputs" / "tables"

COVARIATES = ["age", "male", "bmi", "C(asa)", "emop", "C(optype)", "opdur_min",
              "intraop_crystalloid", "intraop_colloid", "vasopressor_use"]
COV_STR = " + ".join(COVARIATES)
COV_STR_LOGIT = COV_STR.replace("C(optype)", "C(optype_collapsed)")


def holm_bonferroni(pvals_dict, alpha=0.05):
    """Standard Holm step-down procedure. pvals_dict: {label: p}."""
    items = sorted(pvals_dict.items(), key=lambda kv: kv[1])
    m = len(items)
    rows = []
    reject_all_below = True
    for i, (label, p) in enumerate(items):
        threshold = alpha / (m - i)
        reject = reject_all_below and (p < threshold)
        if not reject:
            reject_all_below = False
        rows.append([label, p, threshold, "reject" if reject else "fail to reject"])
    return pd.DataFrame(rows, columns=["Outcome", "p-value", "Holm threshold", "Decision"])


def fit_aki_model(df):
    print("=" * 70)
    print("AKI (KDIGO, corrected staging): logistic regression")
    print("=" * 70)
    sub = df.dropna(subset=["aki_any"]).copy()
    print(f"N = {len(sub)} (of {len(df)}; {sub['aki_any'].notna().sum()} have valid AKI staging)")
    print(f"AKI events: {int(sub['aki_any'].sum())} ({sub['aki_any'].mean():.1%})")

    f = f"aki_any ~ hypothermia_burden + min_core_temp + {COV_STR_LOGIT}"
    m = smf.logit(f, data=sub).fit(disp=0)
    print(f"Converged: {m.mle_retvals['converged']}")
    print(m.summary())

    b, p = m.params["hypothermia_burden"], m.pvalues["hypothermia_burden"]
    ci = np.exp(m.conf_int().loc["hypothermia_burden"])
    print(f"\nburden: OR={np.exp(b):.4f} (95% CI {ci[0]:.4f}-{ci[1]:.4f}), p={p:.4f}")
    sd = sub["hypothermia_burden"].std()
    print(f"burden per SD ({sd:.1f}): OR={np.exp(b*sd):.4f} "
          f"(95% CI {np.exp((b-1.96*m.bse['hypothermia_burden'])*sd):.4f}-"
          f"{np.exp((b+1.96*m.bse['hypothermia_burden'])*sd):.4f})")
    print()
    return m, p


def fit_los_model(df):
    print("=" * 70)
    print("LOS (postoperative days, dis-opend anchor): log-linear OLS")
    print("(continuous fractional days -- log-linear chosen over negative")
    print(" binomial, which assumes integer counts; right-skew handled by log)")
    print("=" * 70)
    sub = df.dropna(subset=["los_postop_days"]).copy()
    sub = sub[sub["los_postop_days"] > 0]  # already nulled the 2 negative-anomaly cases upstream
    sub["log_los"] = np.log(sub["los_postop_days"])
    print(f"N = {len(sub)} (of {len(df)})")

    f = f"log_los ~ hypothermia_burden + min_core_temp + {COV_STR}"
    m = smf.ols(f, data=sub).fit()
    print(m.summary())

    b, p = m.params["hypothermia_burden"], m.pvalues["hypothermia_burden"]
    pct_change_per_100 = (np.exp(b * 100) - 1) * 100
    print(f"\nburden: beta={b:.6f}, p={p:.4f}")
    print(f"burden per 100 units: {pct_change_per_100:+.1f}% change in LOS "
          f"(95% CI {(np.exp((b-1.96*m.bse['hypothermia_burden'])*100)-1)*100:+.1f}% to "
          f"{(np.exp((b+1.96*m.bse['hypothermia_burden'])*100)-1)*100:+.1f}%)")
    print()
    return m, p


def fit_icu_admission_model(df):
    print("=" * 70)
    print("ICU admission (any, icu_days>0): logistic regression [supplementary]")
    print("(icu_days is 70.5% zero -- modeled as binary admission, not a count/")
    print(" duration model, given the zero-inflation)")
    print("=" * 70)
    sub = df.copy()
    sub["icu_admit"] = (sub["icu_days"] > 0).astype(int)
    f = f"icu_admit ~ hypothermia_burden + min_core_temp + {COV_STR_LOGIT}"
    m = smf.logit(f, data=sub).fit(disp=0)
    print(f"Converged: {m.mle_retvals['converged']}")
    b, p = m.params["hypothermia_burden"], m.pvalues["hypothermia_burden"]
    ci = np.exp(m.conf_int().loc["hypothermia_burden"])
    print(f"burden: OR={np.exp(b):.4f} (95% CI {ci[0]:.4f}-{ci[1]:.4f}), p={p:.4f}")
    print()
    return m


def fit_coagulation_models(df):
    print("=" * 70)
    print("Coagulation deltas (Aim 2, EXPLORATORY -- no multiplicity correction)")
    print("=" * 70)
    rows = []
    for outcome, label in [("delta_ptinr", "Delta PT-INR"), ("delta_aptt", "Delta aPTT"), ("delta_fib", "Delta fibrinogen")]:
        sub = df.dropna(subset=[outcome])
        f = f"{outcome} ~ hypothermia_burden + min_core_temp + {COV_STR}"
        m = smf.ols(f, data=sub).fit()
        b, p = m.params["hypothermia_burden"], m.pvalues["hypothermia_burden"]
        ci = m.conf_int().loc["hypothermia_burden"]
        print(f"{label} (N={int(m.nobs)}): beta={b:.6f} (95% CI [{ci[0]:.6f}, {ci[1]:.6f}]), "
              f"p={p:.4f} [exploratory, uncorrected]")
        rows.append([label, int(m.nobs), b, ci[0], ci[1], p])
    tbl = pd.DataFrame(rows, columns=["Outcome", "N", "Beta (burden)", "CI_low", "CI_high", "p-value (uncorrected)"])
    tbl.to_csv(TABLES_DIR / "table4_coagulation_exploratory.csv", index=False)
    print(f"\nSaved -> {TABLES_DIR / 'table4_coagulation_exploratory.csv'}")
    print()


def mortality_descriptive(df):
    print("=" * 70)
    print("Mortality: DESCRIPTIVE ONLY (17 events, not modeled)")
    print("=" * 70)
    d = df.copy()
    d["burden_tertile"] = pd.qcut(d["hypothermia_burden"], 3, labels=["T1 (low)", "T2 (mid)", "T3 (high)"])
    tab = d.groupby("burden_tertile", observed=True)["death_inhosp"].agg(["sum", "count"])
    tab["pct"] = (tab["sum"] / tab["count"] * 100).round(2)
    print(tab)
    tab.to_csv(TABLES_DIR / "table7_mortality_descriptive.csv")
    print(f"\nSaved -> {TABLES_DIR / 'table7_mortality_descriptive.csv'}")
    print()


def main():
    df = pd.read_parquet(DATA_DIR / "analysis_primary_data.parquet")
    print(f"N = {len(df)}")
    print()

    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    m_aki, p_aki = fit_aki_model(df)
    m_los, p_los = fit_los_model(df)
    fit_icu_admission_model(df)
    fit_coagulation_models(df)
    mortality_descriptive(df)

    print("=" * 70)
    print("TABLE 5: AKI and LOS models (burden term)")
    print("=" * 70)
    term = "hypothermia_burden"
    b_aki, ci_aki = m_aki.params[term], m_aki.conf_int().loc[term]
    b_los, ci_los = m_los.params[term], m_los.conf_int().loc[term]
    t5 = pd.DataFrame([
        ["AKI (logistic, KDIGO corrected)", int(m_aki.nobs), f"OR={np.exp(b_aki):.4f}",
         f"[{np.exp(ci_aki[0]):.4f}, {np.exp(ci_aki[1]):.4f}]", f"{p_aki:.4f}"],
        ["LOS (log-linear, dis-opend)", int(m_los.nobs), f"beta={b_los:.6f}",
         f"[{ci_los[0]:.6f}, {ci_los[1]:.6f}]", f"{p_los:.4f}"],
    ], columns=["Outcome", "N", "Estimate (burden)", "95% CI", "p-value"])
    print(t5.to_string(index=False))
    t5.to_csv(TABLES_DIR / "table5_aki_los_models.csv", index=False)
    print(f"\nSaved -> {TABLES_DIR / 'table5_aki_los_models.csv'}")
    print()

    print("=" * 70)
    print("Holm-Bonferroni correction: AKI + LOS only (2-test family)")
    print("(coagulation excluded -- exploratory framing, not a confirmatory")
    print(" test family; bundling it in would overstate its evidentiary status)")
    print("=" * 70)
    holm = holm_bonferroni({"AKI (burden)": p_aki, "LOS (burden)": p_los})
    print(holm.to_string(index=False))
    holm.to_csv(TABLES_DIR / "table5b_holm_bonferroni.csv", index=False)
    print(f"\nSaved -> {TABLES_DIR / 'table5b_holm_bonferroni.csv'}")


if __name__ == "__main__":
    main()
