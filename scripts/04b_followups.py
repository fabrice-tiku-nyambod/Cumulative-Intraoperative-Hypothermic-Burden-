"""
Three bounded follow-ups on 04's Aim 1 results, locked as SS6b -- all
re-expressions/visualizations of what's already fitted, no new modeling
beyond a tertile-categorical recode and per-stratum refits:

1. Re-express the transfusion OR (1.0028/unit -- not clinically interpretable
   as-is) per SD, per 100 units, and top-vs-bottom burden tertile.
2. Plot the RCS dose-response curve so the nonlinearity (p=0.011) has an
   actual shape attached, not just a p-value.
3. Stratified burden coefficient (stomach vs. non-stomach) to put a point
   estimate + CI behind the significant interaction (p=0.036).
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
TABLES_DIR = PROJECT_DIR / "outputs" / "tables"
FIGURES_DIR = PROJECT_DIR / "outputs" / "figures"

COVARIATES = ["age", "male", "bmi", "C(asa)", "emop", "C(optype)", "opdur_min",
              "intraop_crystalloid", "intraop_colloid", "vasopressor_use"]
COV_STR = " + ".join(COVARIATES)
COV_STR_LOGIT = COV_STR.replace("C(optype)", "C(optype_collapsed)")

# validated dataviz palette: single sequential hue (blue), line + lighter CI band
LINE_COLOR = "#1f5fa8"
BAND_COLOR = "#a9c6e8"
TEXT_COLOR = "#2a2a2a"
CI_EDGE_COLOR = "#e8a33d"  # warm accent, separates "uncertainty" (CI) from "estimate" (line)
RUG_COLOR = "#888888"


def rcs_basis(x, knots):
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


def followup_1_or_reexpression(df):
    print("=" * 70)
    print("FOLLOW-UP 1: Transfusion OR re-expressed in interpretable units")
    print("=" * 70)
    f_logit = f"transfused ~ hypothermia_burden + min_core_temp + {COV_STR_LOGIT}"
    m = smf.logit(f_logit, data=df).fit(disp=0)

    beta = m.params["hypothermia_burden"]
    se = m.bse["hypothermia_burden"]
    sd = df["hypothermia_burden"].std()

    print(f"burden distribution: mean={df['hypothermia_burden'].mean():.1f}, sd={sd:.1f}, "
          f"median={df['hypothermia_burden'].median():.1f}, "
          f"IQR=[{df['hypothermia_burden'].quantile(.25):.1f}, {df['hypothermia_burden'].quantile(.75):.1f}], "
          f"range=[{df['hypothermia_burden'].min():.1f}, {df['hypothermia_burden'].max():.1f}]")
    print()

    for label, increment in [("per 1 unit (as originally reported)", 1),
                              ("per 100 units", 100),
                              ("per 1 SD", sd)]:
        or_val = np.exp(beta * increment)
        ci_lo = np.exp((beta - 1.96 * se) * increment)
        ci_hi = np.exp((beta + 1.96 * se) * increment)
        print(f"  {label} (+{increment:.1f}): OR={or_val:.3f} (95% CI {ci_lo:.3f}-{ci_hi:.3f})")

    # Top-vs-bottom tertile: fit directly on tertile category, not extrapolated
    # from the continuous beta, since that avoids assuming linearity holds all
    # the way out to the tertile extremes.
    df2 = df.copy()
    df2["burden_tertile"] = pd.qcut(df2["hypothermia_burden"], 3, labels=["T1", "T2", "T3"])
    f_tertile = f"transfused ~ C(burden_tertile, Treatment('T1')) + min_core_temp + {COV_STR_LOGIT}"
    m_tert = smf.logit(f_tertile, data=df2).fit(disp=0)
    term = "C(burden_tertile, Treatment('T1'))[T.T3]"
    or_t3 = np.exp(m_tert.params[term])
    ci = np.exp(m_tert.conf_int().loc[term])
    print(f"  Top (T3) vs bottom (T1) tertile: OR={or_t3:.3f} (95% CI {ci[0]:.3f}-{ci[1]:.3f}), "
          f"p={m_tert.pvalues[term]:.4f}")

    out = pd.DataFrame([
        ["Per 1 unit", np.exp(beta), np.exp(beta - 1.96 * se), np.exp(beta + 1.96 * se)],
        ["Per 100 units", np.exp(beta * 100), np.exp((beta - 1.96 * se) * 100), np.exp((beta + 1.96 * se) * 100)],
        ["Per 1 SD", np.exp(beta * sd), np.exp((beta - 1.96 * se) * sd), np.exp((beta + 1.96 * se) * sd)],
        ["Top vs bottom tertile", or_t3, ci[0], ci[1]],
    ], columns=["Increment", "OR", "CI_low", "CI_high"])
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(TABLES_DIR / "table2b_transfusion_or_reexpressed.csv", index=False)
    print(f"\nSaved -> {TABLES_DIR / 'table2b_transfusion_or_reexpressed.csv'}")
    print()


def followup_2_rcs_plot(df):
    print("=" * 70)
    print("FOLLOW-UP 2: RCS dose-response curve, burden -> EBL")
    print("=" * 70)
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

    # Predict across the observed range (5th-95th pctile, not extrapolated beyond data),
    # holding covariates at reference values (means for continuous, mode for categorical).
    lo, hi = np.percentile(x, [5, 95])
    grid = np.linspace(lo, hi, 200)
    grid_basis = rcs_basis(grid, knots)

    ref = {c: df2[c].mean() for c in ["min_core_temp", "age", "bmi", "opdur_min",
                                        "intraop_crystalloid", "intraop_colloid"]}
    ref["male"] = df2["male"].mode()[0]
    ref["emop"] = 0
    ref["vasopressor_use"] = df2["vasopressor_use"].mode()[0]
    ref["asa"] = df2["asa"].mode()[0]
    ref["optype"] = df2["optype"].mode()[0]

    pred_df = pd.DataFrame({
        "hypothermia_burden": grid,
        "_rcs1": grid_basis[:, 1],
        "_rcs2": grid_basis[:, 2],
        **{k: v for k, v in ref.items()},
    })
    pred = m_rcs.get_prediction(pred_df).summary_frame(alpha=0.05)

    ebl_mean = np.expm1(pred["mean"])
    ebl_lo = np.expm1(pred["mean_ci_lower"])
    ebl_hi = np.expm1(pred["mean_ci_upper"])

    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    ax.fill_between(grid, ebl_lo, ebl_hi, color=BAND_COLOR, alpha=0.6, linewidth=0, label="95% CI")
    # Warm-accent CI edges, distinct from the blue estimate line, so "uncertainty
    # boundary" and "point estimate" read as two different things at a glance.
    ax.plot(grid, ebl_lo, color=CI_EDGE_COLOR, linewidth=0.9, alpha=0.8, zorder=2)
    ax.plot(grid, ebl_hi, color=CI_EDGE_COLOR, linewidth=0.9, alpha=0.8, zorder=2)
    ax.plot(grid, ebl_mean, color=LINE_COLOR, linewidth=2.5, zorder=3)

    # Rug plot: where the actual burden observations sit, so a reader can tell
    # whether the curve's wiggle near the tails is real signal or just sparse
    # data out there -- a legitimate reviewer question this dataset can answer
    # for free, without needing the raw data themselves.
    y_min, y_max = ax.get_ylim()
    rug_y0 = y_min - 0.03 * (y_max - y_min)
    rug_y1 = y_min
    x_obs = df["hypothermia_burden"].values
    x_obs_in_range = x_obs[(x_obs >= grid[0]) & (x_obs <= grid[-1])]
    ax.vlines(x_obs_in_range, rug_y0, rug_y1, color=RUG_COLOR, linewidth=0.4, alpha=0.35, zorder=1, clip_on=False)
    ax.set_ylim(rug_y0, y_max)

    ax.set_xlabel("Hypothermia burden (degree-minutes <36.0°C)", color=TEXT_COLOR)
    ax.set_ylabel("Predicted intraoperative EBL, mL\n(covariates at reference values)", color=TEXT_COLOR)
    ax.set_title(f"Restricted cubic spline: hypothermia burden vs. blood loss\n(nonlinearity LRT p={p_nonlin:.3f})",
                 color=TEXT_COLOR, fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#888888")
    ax.tick_params(colors=TEXT_COLOR)
    ax.grid(axis="y", color="#e5e5e5", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / "figure3_rcs_dose_response.png", facecolor="white")
    plt.close(fig)

    # Describe the shape numerically rather than just eyeballing the PNG.
    slope_early = (ebl_mean.iloc[50] - ebl_mean.iloc[0]) / (grid[50] - grid[0])
    slope_late = (ebl_mean.iloc[-1] - ebl_mean.iloc[-50]) / (grid[-1] - grid[-50])
    print(f"Predicted EBL at burden={grid[0]:.0f} (5th pctile): {ebl_mean.iloc[0]:.0f} mL")
    print(f"Predicted EBL at burden={grid[100]:.0f} (median-ish): {ebl_mean.iloc[100]:.0f} mL")
    print(f"Predicted EBL at burden={grid[-1]:.0f} (95th pctile): {ebl_mean.iloc[-1]:.0f} mL")
    print(f"Approx slope, low end of range: {slope_early:.2f} mL per unit burden")
    print(f"Approx slope, high end of range: {slope_late:.2f} mL per unit burden")
    print(f"Nonlinearity LRT p-value (RCS vs linear): {p_nonlin:.4f}")
    print(f"Saved -> {FIGURES_DIR / 'figure3_rcs_dose_response.png'}")

    rcs_tbl = pd.DataFrame([{
        "burden_5th_pctile": grid[0], "ebl_pred_5th_mL": ebl_mean.iloc[0],
        "burden_median_ish": grid[100], "ebl_pred_median_mL": ebl_mean.iloc[100],
        "burden_95th_pctile": grid[-1], "ebl_pred_95th_mL": ebl_mean.iloc[-1],
        "peak_to_trough_mL": ebl_mean.max() - ebl_mean.min(),
        "ci_band_width_min_mL": (ebl_hi - ebl_lo).min(), "ci_band_width_max_mL": (ebl_hi - ebl_lo).max(),
        "nonlinearity_LRT_p": p_nonlin,
        "reference_profile_optype": ref["optype"],
    }])
    rcs_tbl.to_csv(TABLES_DIR / "figure3_rcs_values.csv", index=False)
    print(f"Saved -> {TABLES_DIR / 'figure3_rcs_values.csv'}")
    print()


def followup_3_stratified_interaction(df):
    print("=" * 70)
    print("FOLLOW-UP 3: Burden effect stratified by Stomach vs. non-Stomach")
    print("=" * 70)
    # optype dropped within the stomach-only stratum: it's constant there
    # (all Stomach), so it can't contribute a coefficient.
    cov_no_optype = " + ".join(c for c in COVARIATES if c != "C(optype)")
    f_strat = f"log_ebl ~ hypothermia_burden + min_core_temp + {cov_no_optype}"

    rows = []
    for label, subset in [("Stomach", df[df["is_stomach"] == 1]),
                           ("Non-Stomach", df[df["is_stomach"] == 0])]:
        m = smf.ols(f_strat, data=subset).fit()
        b, p = m.params["hypothermia_burden"], m.pvalues["hypothermia_burden"]
        ci = m.conf_int().loc["hypothermia_burden"]
        rows.append([label, int(m.nobs), round(b, 5), round(ci[0], 5), round(ci[1], 5), round(p, 4)])
        print(f"{label} (N={int(m.nobs)}): beta={b:.5f} (95% CI [{ci[0]:.5f}, {ci[1]:.5f}]), p={p:.4f}")

    tbl = pd.DataFrame(rows, columns=["Stratum", "N", "Beta (burden)", "CI_low", "CI_high", "p-value"])
    tbl.to_csv(TABLES_DIR / "table2c_stratified_burden_effect.csv", index=False)
    print(f"\nSaved -> {TABLES_DIR / 'table2c_stratified_burden_effect.csv'}")
    print("\nNote: opposite-signed, non-overlapping-ish point estimates here would explain")
    print("the significant interaction term better than either stratum's p-value alone.")
    print()


def main():
    df = pd.read_parquet(DATA_DIR / "analysis_primary_data.parquet")
    print(f"N = {len(df)}")
    print()
    followup_1_or_reexpression(df)
    followup_2_rcs_plot(df)
    followup_3_stratified_interaction(df)


if __name__ == "__main__":
    main()
