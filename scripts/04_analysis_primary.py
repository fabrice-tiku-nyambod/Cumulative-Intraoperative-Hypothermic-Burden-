"""
Aim 1 primary analysis: hypothermia burden vs. intraoperative blood loss and
transfusion requirement. Pure local computation on cached parquet files --
no API calls, no benchmark/checkpoint machinery needed.

Cohort: final analytic cohort (N=2,568) minus 1 ASA=6 (organ-donor,
physiologically non-comparable) case -> N=2,567, per locked decision.
ane_type dropped from covariates (2,567:1 split in this cohort, no real
variance to adjust on -- an artifact of the >=120min duration inclusion
criterion selecting almost exclusively general anesthesia).

Complete-case throughout (per SS7.8): statsmodels formula API listwise-
deletes rows with NaN in any formula variable.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from patsy import dmatrices
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
TABLES_DIR = PROJECT_DIR / "outputs" / "tables"
FIGURES_DIR = PROJECT_DIR / "outputs" / "figures"

COVARIATES = ["age", "male", "bmi", "C(asa)", "emop", "C(optype)", "opdur_min",
              "intraop_crystalloid", "intraop_colloid", "vasopressor_use"]
COV_STR = " + ".join(COVARIATES)


# ---------------------------------------------------------------- data -----

def load_analysis_data():
    final = pd.read_parquet(DATA_DIR / "final_exposure_cohort.parquet")
    outcomes = pd.read_parquet(DATA_DIR / "outcomes.parquet")
    cand = pd.read_parquet(DATA_DIR / "candidate_cohort.parquet")

    exposure_cols = ["caseid", "hypothermia_burden", "min_core_temp", "min_core_temp_smoothed",
                      "early_thermal_drop_velocity", "hypothermia_duration_min", "pre_monitoring_gap_sec"]
    cov_cols = ["caseid", "age", "sex", "bmi", "asa", "emop", "optype", "opdur_min",
                "intraop_crystalloid", "intraop_colloid", "intraop_eph", "intraop_phe", "intraop_epi"]

    df = final[exposure_cols].merge(outcomes, on="caseid", how="inner")
    df = df.merge(cand[cov_cols], on="caseid", how="left")
    assert len(df) == 2568, f"expected 2568 pre-ASA-exclusion, got {len(df)}"

    n_before = len(df)
    df = df[df["asa"] != 6].copy()
    print(f"Excluded {n_before - len(df)} ASA=6 (organ donor) case(s): N={n_before} -> {len(df)}")

    df["male"] = (df["sex"] == "M").astype(int)
    df["is_stomach"] = (df["optype"] == "Stomach").astype(int)
    df["vasopressor_use"] = ((df["intraop_eph"] > 0) | (df["intraop_phe"] > 0) | (df["intraop_epi"] > 0)).astype(int)
    df["log_ebl"] = np.log1p(df["intraop_ebl"])
    df["transfused"] = df["transfused"].astype(int)

    # Logistic-model-only: Thyroid (0/87) and Breast (0/67) optype categories have
    # zero transfusion events, causing quasi-complete separation (coef ~-18,
    # SE ~4000). Merged into the existing "Others" category (52/221 events),
    # NOT into each other -- merging two zero-event categories together still
    # yields a zero-event category (0+0=0), which doesn't fix separation at all.
    zero_event_optypes = {"Thyroid", "Breast"}
    df["optype_collapsed"] = df["optype"].apply(lambda x: "Others" if x in zero_event_optypes else x)
    return df


# ------------------------------------------------------------- RCS basis ---

def rcs_basis(x, knots):
    """Harrell's restricted cubic spline basis. Returns an (n, k-1) array:
    column 0 is the linear term, columns 1..k-2 are the nonlinear terms."""
    x = np.asarray(x, dtype=float)
    k = len(knots)
    t = knots

    def pos(u):
        return np.where(u > 0, u, 0.0)

    cols = [x]
    for j in range(k - 2):
        term = (pos(x - t[j]) ** 3
                - pos(x - t[k - 2]) ** 3 * (t[k - 1] - t[j]) / (t[k - 1] - t[k - 2])
                + pos(x - t[k - 1]) ** 3 * (t[k - 2] - t[j]) / (t[k - 1] - t[k - 2]))
        cols.append(term / (t[k - 1] - t[0]) ** 2)
    return np.column_stack(cols)


# --------------------------------------------------------------- Table 1 ---

def table1_by_tertile(df):
    df = df.copy()
    df["burden_tertile"] = pd.qcut(df["hypothermia_burden"], 3, labels=["T1 (low)", "T2 (mid)", "T3 (high)"])
    cats = list(df["burden_tertile"].cat.categories)
    rows = []

    for label, col in [("Age, years", "age"), ("BMI, kg/m2", "bmi"), ("Op duration, min", "opdur_min"),
                        ("Intraop EBL, mL", "intraop_ebl"), ("Crystalloid, mL", "intraop_crystalloid")]:
        g = df.groupby("burden_tertile", observed=True)[col]
        groups = [df.loc[df["burden_tertile"] == t, col].dropna() for t in cats]
        _, p = stats.f_oneway(*groups)
        rows.append([label] + [f"{g.mean()[t]:.1f} +/- {g.std()[t]:.1f}" for t in cats] + [f"{p:.4f}"])

    for label, col, val in [("Male sex", "male", 1), ("Emergency op", "emop", 1),
                             ("Stomach optype", "is_stomach", 1), ("Any transfusion", "transfused", True)]:
        pct = df.groupby("burden_tertile", observed=True)[col].apply(lambda s: (s == val).mean())
        tab = pd.crosstab(df["burden_tertile"], df[col] == val)
        _, p, _, _ = stats.chi2_contingency(tab)
        rows.append([label] + [f"{pct[t]:.1%}" for t in cats] + [f"{p:.4f}"])

    tbl = pd.DataFrame(rows, columns=["Characteristic"] + cats + ["p-value"])
    return tbl, df[["caseid", "burden_tertile"]]


# ---------------------------------------------------------- primary models -
#
# early_thermal_drop_velocity is only 62.1% complete (needs >=2 valid BT
# readings in the first 30 min of the anesthesia window) and collapses the
# fully-adjusted model from N~2,089 to N=1,276 if bundled in. Per locked
# decision: dropped from the primary spec, reported separately at its own
# natural N via fit_thermal_velocity_comparator() below. The primary
# exposure comparison is burden vs. min_core_temp only.
#
# Logistic model uses optype_collapsed (Thyroid+Breast -> Other/low-volume)
# to avoid quasi-complete separation from their zero transfusion events;
# the linear model uses optype at full granularity since EBL is continuous.

COV_STR_LOGIT = COV_STR.replace("C(optype)", "C(optype_collapsed)")


def fit_primary_models(df):
    f_linear = f"log_ebl ~ hypothermia_burden + min_core_temp + {COV_STR}"
    f_logit = f"transfused ~ hypothermia_burden + min_core_temp + {COV_STR_LOGIT}"
    m_linear = smf.ols(f_linear, data=df).fit()
    m_logit = smf.logit(f_logit, data=df).fit(disp=0)
    return m_linear, m_logit, f_linear, f_logit


def fit_thermal_velocity_comparator(df):
    """early_thermal_drop_velocity reported separately at its own natural N,
    per the locked decision -- not bundled into the primary model."""
    f = f"log_ebl ~ early_thermal_drop_velocity + {COV_STR}"
    df_avail = df.dropna(subset=["early_thermal_drop_velocity"])
    m = smf.ols(f, data=df).fit()
    return m, f, len(df_avail)


def nested_model_comparison(df):
    """Models 1-3 only (baseline -> +min_temp -> +burden). Thermal-drop-
    velocity is excluded from this hierarchy entirely -- bundling it back in
    as a 'Model 4' would reintroduce the N-mismatch that made the original
    4-model LRT chain invalid (Model 4 fit on a different, smaller sample
    than Models 1-3 makes their AIC/BIC/LRT incomparable)."""
    formulas = {
        "Model 1 (baseline)": f"log_ebl ~ {COV_STR}",
        "Model 2 (+min temp)": f"log_ebl ~ {COV_STR} + min_core_temp",
        "Model 3 (+burden)": f"log_ebl ~ {COV_STR} + min_core_temp + hypothermia_burden",
    }
    rows, fitted = [], {}
    prev_llf = prev_df = None
    ns = set()
    for name, f in formulas.items():
        m = smf.ols(f, data=df).fit()
        fitted[name] = m
        ns.add(int(m.nobs))
        lrt_p = np.nan
        if prev_llf is not None:
            lr_stat = 2 * (m.llf - prev_llf)
            df_diff = m.df_model - prev_df
            lrt_p = stats.chi2.sf(lr_stat, df_diff) if df_diff > 0 else np.nan
        rows.append([name, int(m.nobs), round(m.rsquared, 4), round(m.aic, 1), round(m.bic, 1),
                     f"{lrt_p:.4f}" if pd.notna(lrt_p) else "--"])
        prev_llf, prev_df = m.llf, m.df_model
    assert len(ns) == 1, f"nested models fit on different N: {ns} -- LRT chain is invalid"
    return pd.DataFrame(rows, columns=["Model", "N", "R2", "AIC", "BIC", "LRT p (vs prior)"]), fitted


def rcs_dose_response(df):
    x = df["hypothermia_burden"].values
    knots = np.percentile(x, [5, 35, 65, 95])
    basis = rcs_basis(x, knots)
    df2 = df.copy()
    df2["_rcs1"], df2["_rcs2"] = basis[:, 1], basis[:, 2]

    f_rcs = f"log_ebl ~ hypothermia_burden + _rcs1 + _rcs2 + min_core_temp + {COV_STR}"
    f_lin = f"log_ebl ~ hypothermia_burden + min_core_temp + {COV_STR}"
    m_rcs = smf.ols(f_rcs, data=df2).fit()
    m_lin = smf.ols(f_lin, data=df2).fit()

    lr_stat = 2 * (m_rcs.llf - m_lin.llf)
    df_diff = m_rcs.df_model - m_lin.df_model
    p_nonlin = stats.chi2.sf(lr_stat, df_diff)
    return m_rcs, p_nonlin, knots, df2


def stomach_interaction(df):
    f = f"log_ebl ~ hypothermia_burden * is_stomach + min_core_temp + {COV_STR}"
    return smf.ols(f, data=df).fit()


def early_gap_sensitivity(df, formula):
    sub = df[df["pre_monitoring_gap_sec"] <= 1800]
    m = smf.ols(formula, data=sub).fit()
    return m, len(sub)


def vif_diagnostics(df, formula):
    y, X = dmatrices(formula, data=df, return_type="dataframe")
    vifs = pd.Series(
        [variance_inflation_factor(X.values, i) for i in range(X.shape[1])],
        index=X.columns,
    )
    return vifs.drop("Intercept")


# ------------------------------------------------------------------ main ---

def main():
    df = load_analysis_data()
    print(f"Analysis N: {len(df)}")
    print()

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("TABLE 1: Baseline characteristics by hypothermia-burden tertile")
    print("=" * 70)
    t1, tertile_map = table1_by_tertile(df)
    print(t1.to_string(index=False))
    t1.to_csv(TABLES_DIR / "table1_baseline_by_tertile.csv", index=False)
    print()

    print("=" * 70)
    print("TABLE 2: Fully adjusted primary models (Aim 1) -- burden + min_core_temp")
    print("(early_thermal_drop_velocity excluded here; see comparator model below)")
    print("=" * 70)
    m_linear, m_logit, f_linear, f_logit = fit_primary_models(df)
    print(f"Linear model N = {int(m_linear.nobs)}, Logistic model N = {int(m_logit.nobs)}")
    print("--- Linear model: log(EBL+1) ---")
    print(m_linear.summary())
    print()
    print("--- Logistic model: transfusion (optype_collapsed: Thyroid+Breast -> Other/low-volume) ---")
    print(m_logit.summary())
    key_rows = []
    for label, m, is_logit in [("Linear (log EBL)", m_linear, False), ("Logistic (transfusion)", m_logit, True)]:
        for term in ["hypothermia_burden", "min_core_temp"]:
            coef, p = m.params[term], m.pvalues[term]
            ci = m.conf_int().loc[term]
            if is_logit:
                key_rows.append([label, term, np.exp(coef), np.exp(ci[0]), np.exp(ci[1]), p,
                                  f"OR={np.exp(coef):.4f}", f"{p:.4f}"])
            else:
                key_rows.append([label, term, coef, ci[0], ci[1], p,
                                  f"beta={coef:.5f}", f"{p:.4f}"])
    pd.DataFrame(key_rows, columns=["Model", "Term", "Estimate_raw", "CI_low", "CI_high", "p_raw",
                                     "Estimate", "p-value"]).to_csv(
        TABLES_DIR / "table2_primary_models_key_terms.csv", index=False)
    print()

    print("=" * 70)
    print("Comparator model: early_thermal_drop_velocity (own natural N, not bundled into Table 2)")
    print("=" * 70)
    m_thermal, f_thermal, n_thermal_avail = fit_thermal_velocity_comparator(df)
    print(f"Cases with non-missing early_thermal_drop_velocity: {n_thermal_avail}/{len(df)} "
          f"({n_thermal_avail/len(df):.1%}); model fit N = {int(m_thermal.nobs)}")
    term = "early_thermal_drop_velocity"
    print(f"{term}: beta={m_thermal.params[term]:.5f}, p={m_thermal.pvalues[term]:.4f}, "
          f"95% CI [{m_thermal.conf_int().loc[term,0]:.5f}, {m_thermal.conf_int().loc[term,1]:.5f}]")
    print()

    print("=" * 70)
    print("TABLE 3: Nested model comparison (Model 1->3: baseline -> +min_temp -> +burden)")
    print("=" * 70)
    t3, fitted_models = nested_model_comparison(df)
    print(t3.to_string(index=False))
    t3.to_csv(TABLES_DIR / "table3_nested_model_comparison.csv", index=False)
    print()

    print("=" * 70)
    print("Restricted cubic spline dose-response (burden -> log EBL)")
    print("=" * 70)
    m_rcs, p_nonlin, knots, df_rcs = rcs_dose_response(df)
    print(f"Knots (5/35/65/95th pctile of burden): {knots}")
    print(f"Nonlinearity LRT p-value (RCS vs linear): {p_nonlin:.4f}")
    print()

    print("=" * 70)
    print("Burden x Stomach-surgery interaction")
    print("=" * 70)
    m_int = stomach_interaction(df)
    int_term = "hypothermia_burden:is_stomach"
    print(f"Interaction term ({int_term}): beta={m_int.params[int_term]:.5f}, p={m_int.pvalues[int_term]:.4f}")
    print()

    print("=" * 70)
    print("Sensitivity subset: pre-monitoring gap <= 30 min")
    print("=" * 70)
    m_sens, n_sens = early_gap_sensitivity(df, f_linear)
    print(f"Subset N = {n_sens} (vs full N = {len(df)})")
    for term in ["hypothermia_burden", "min_core_temp"]:
        print(f"  {term}: full beta={m_linear.params[term]:.5f} (p={m_linear.pvalues[term]:.4f}) | "
              f"subset beta={m_sens.params[term]:.5f} (p={m_sens.pvalues[term]:.4f})")
    print()

    print("=" * 70)
    print("VIF diagnostics (fully adjusted linear model)")
    print("=" * 70)
    vifs = vif_diagnostics(df, f_linear)
    print(vifs.sort_values(ascending=False).to_string())
    vifs.to_csv(TABLES_DIR / "table6_vif.csv", header=["VIF"])
    print()

    df.to_parquet(DATA_DIR / "analysis_primary_data.parquet", index=False)
    print(f"Analysis dataset saved -> {DATA_DIR / 'analysis_primary_data.parquet'}")


if __name__ == "__main__":
    main()
