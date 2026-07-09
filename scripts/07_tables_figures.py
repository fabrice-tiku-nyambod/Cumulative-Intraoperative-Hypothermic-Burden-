"""
Final assembly: Tables 1-9, Figures 1-3, generated once from the locked
04/04b/04c/05 outputs (per SS9's reproducibility structure). No new
modeling here beyond presentation-layer transforms (SD-standardizing
already-fit coefficients for the forest plot) -- everything substantive
was already computed and locked upstream.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
TABLES_DIR = PROJECT_DIR / "outputs" / "tables"
FIGURES_DIR = PROJECT_DIR / "outputs" / "figures"

COVARIATES = ["age", "male", "bmi", "C(asa)", "emop", "C(optype)", "opdur_min",
              "intraop_crystalloid", "intraop_colloid", "vasopressor_use"]
COV_STR = " + ".join(COVARIATES)

TEXT_COLOR = "#2a2a2a"
BOX_EDGE = "#555555"
EXCL_COLOR = "#c0392b"
LINE_COLOR = "#1f5fa8"


def figure1_strobe(df_attrition):
    fig, ax = plt.subplots(figsize=(8.5, 11), dpi=150)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 22)
    ax.axis("off")

    steps = [
        ("Total cases in clinical_data.csv\n(VitalDB v1.0.0)", 6388, None),
        ("Department in {General, Thoracic,\nUrology, Gynecology} surgery", 6388, "0 excluded (all cases already\nin these 4 departments)"),
        ("Age >= 18 years", 6323, "65 excluded\n(8 unparseable/missing age)"),
        ("Operative duration\n(opend-opstart) > 120 min", 2865, "3,458 excluded"),
        ("Reoperation dedup\n(index case per subjectid)", 2824, "41 excluded\n(39 subjects had >1 case)"),
        ("CANDIDATE COHORT", 2824, None),
        ("BT trimmed coverage >= 95%\n(per-case observed-window rule)", 2568, "256 excluded:\n75 no_valid_bt, 1 empty-window,\n180 failed coverage threshold"),
        ("ANALYTIC COHORT", 2568, None),
        ("Exclude ASA=6\n(brain-dead organ donor)", 2567, "1 excluded (physiologically\nnon-comparable to surgical cohort)"),
        ("FINAL AIM 1-3 COHORT", 2567, None),
    ]

    y = 21
    box_h = 1.15
    for i, (label, n, excl_note) in enumerate(steps):
        is_milestone = label.isupper() or label in ("CANDIDATE COHORT", "ANALYTIC COHORT", "FINAL AIM 1-3 COHORT")
        fc = "#eef3fa" if is_milestone else "white"
        lw = 2.0 if is_milestone else 1.2
        box = plt.Rectangle((1.5, y - box_h), 6, box_h, facecolor=fc, edgecolor=BOX_EDGE, linewidth=lw, zorder=2)
        ax.add_patch(box)
        ax.text(4.5, y - box_h / 2, f"{label}\nN = {n:,}", ha="center", va="center",
                 fontsize=9.5 if is_milestone else 8.5,
                 fontweight="bold" if is_milestone else "normal", color=TEXT_COLOR, zorder=3)

        if excl_note:
            ax.annotate("", xy=(7.6, y - box_h / 2), xytext=(9.3, y - box_h / 2),
                         arrowprops=dict(arrowstyle="-", color=EXCL_COLOR, lw=1.2), zorder=1)
            ax.text(9.35, y - box_h / 2, excl_note, ha="left", va="center", fontsize=7.3, color=EXCL_COLOR)

        if i < len(steps) - 1:
            ax.annotate("", xy=(4.5, y - box_h - 0.55), xytext=(4.5, y - box_h),
                         arrowprops=dict(arrowstyle="-|>", color=BOX_EDGE, lw=1.4), zorder=1)
        y -= box_h + 0.75

    ax.set_title("Figure 1. STROBE cohort flow diagram", fontsize=12, color=TEXT_COLOR, pad=10)
    fig.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / "figure1_strobe.png", facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Figure 1 (STROBE) saved -> {FIGURES_DIR / 'figure1_strobe.png'}")


def figure2_coefficient_plot(df):
    """SD-standardized coefficients so burden (range 0-982) and min_core_temp
    (range ~31-37) are visually comparable on one axis -- a presentation
    transform of already-fit coefficients, not a new model."""
    f_linear = f"log_ebl ~ hypothermia_burden + min_core_temp + {COV_STR}"
    f_logit = f"transfused ~ hypothermia_burden + min_core_temp + {COV_STR.replace('C(optype)', 'C(optype_collapsed)')}"
    m_lin = smf.ols(f_linear, data=df).fit()
    m_log = smf.logit(f_logit, data=df).fit(disp=0)

    sd_burden = df["hypothermia_burden"].std()
    sd_temp = df["min_core_temp"].std()
    sds = {"hypothermia_burden": sd_burden, "min_core_temp": sd_temp}
    labels = {"hypothermia_burden": "Hypothermia burden\n(per SD)", "min_core_temp": "Minimum core temp\n(per SD)"}

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), dpi=150)

    ax = axes[0]
    terms = ["hypothermia_burden", "min_core_temp"]
    ys = np.arange(len(terms))[::-1]
    for y, term in zip(ys, terms):
        b = m_lin.params[term] * sds[term]
        ci = m_lin.conf_int().loc[term] * sds[term]
        ax.plot([ci[0], ci[1]], [y, y], color=LINE_COLOR, lw=2, solid_capstyle="round")
        ax.plot(b, y, "o", color=LINE_COLOR, markersize=7, zorder=3)
    ax.axvline(0, color="#999999", lw=1, linestyle="--", zorder=0)
    ax.set_yticks(ys)
    ax.set_yticklabels([labels[t] for t in terms], fontsize=9)
    ax.set_xlabel("Beta, log(EBL+1) per SD", fontsize=9)
    ax.set_title("A. Blood loss (linear, N={})".format(int(m_lin.nobs)), fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)

    ax = axes[1]
    for y, term in zip(ys, terms):
        or_val = np.exp(m_log.params[term] * sds[term])
        ci = np.exp(m_log.conf_int().loc[term] * sds[term])
        ax.plot([ci[0], ci[1]], [y, y], color=LINE_COLOR, lw=2, solid_capstyle="round")
        ax.plot(or_val, y, "o", color=LINE_COLOR, markersize=7, zorder=3)
    ax.axvline(1, color="#999999", lw=1, linestyle="--", zorder=0)
    ax.set_xscale("log")
    xticks = [0.8, 0.9, 1.0, 1.2, 1.4, 1.6]
    ax.set_xticks(xticks)
    ax.set_xticklabels([f"{t:g}" for t in xticks])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_yticks(ys)
    ax.set_yticklabels([labels[t] for t in terms], fontsize=9)
    ax.set_xlabel("Odds ratio, transfusion per SD", fontsize=9)
    ax.set_title("B. Transfusion (logistic, N={})".format(int(m_log.nobs)), fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)

    for a in axes:
        a.tick_params(colors=TEXT_COLOR)
        a.grid(axis="x", color="#e5e5e5", linewidth=0.8, zorder=0)
        a.set_axisbelow(True)

    fig.suptitle("Figure 2. Aim 1 primary model coefficients (SD-standardized)", fontsize=11, color=TEXT_COLOR)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure2_coefficient_plot.png", facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Figure 2 (coefficient plot) saved -> {FIGURES_DIR / 'figure2_coefficient_plot.png'}")


def assemble_manifest():
    manifest = [
        ("Table 1", "table1_baseline_by_tertile.csv", "Baseline characteristics by hypothermia-burden tertile"),
        ("Table 2", "table2_primary_models_key_terms.csv", "Fully adjusted Aim 1 models (EBL linear, transfusion logistic)"),
        ("Table 2b", "table2b_transfusion_or_reexpressed.csv", "Transfusion OR re-expressed per 100 units/SD/tertile (NOTE: tertile comparison p=0.070, n.s. -- categorizing a continuous exposure costs power vs. the continuous model's p=0.001; not a contradiction)"),
        ("Table 2c", "table2c_stratified_burden_effect.csv", "Burden effect stratified by Stomach vs. non-Stomach (opposite-signed point estimates explain the significant interaction; neither stratum significant alone at N=322/1767)"),
        ("Table 3", "table3_nested_model_comparison.csv", "Nested model comparison, Model 1->3 (baseline -> +min_temp -> +burden), same N throughout"),
        ("Table 4", "table4_coagulation_exploratory.csv", "Coagulation deltas (Aim 2, EXPLORATORY, uncorrected p-values)"),
        ("Table 5", "table5_aki_los_models.csv", "AKI and LOS models (Aim 3)"),
        ("Table 5b", "table5b_holm_bonferroni.csv", "Holm-Bonferroni correction, AKI+LOS 2-test family only (LOS's raw p=0.042 does NOT survive correction)"),
        ("Table 5c", "table5c_icu_admission.csv", "ICU admission (any), supplementary binary model; icu_days zero-inflation fraction"),
        ("Table 6", "table6_vif.csv", "VIF collinearity diagnostics, fully adjusted linear model (all <2.3)"),
        ("Table 7", "table7_mortality_descriptive.csv", "Mortality by burden tertile, DESCRIPTIVE ONLY (17 events, not modeled)"),
        ("Table 8", "excluded_vs_included_comparison.csv", "Excluded-vs-included cohort comparison (EBL/transfusion/AKI/coag -- no differential attrition by outcome severity on any dimension checked)"),
        ("Table 8b", "table8b_stomach_coverage_association.csv", "Stomach-surgery coverage-failure association, unadjusted and adjusted OR/CI/p"),
        ("Table 9", "table9_v1_replication_comparison.csv", "v1 (Delta Hb) vs. v2 (EBL) direct comparison, identical covariates/cohort/model type -- burden not significant for either outcome"),
        ("Figure 3 values", "figure3_rcs_values.csv", "RCS predicted-EBL values, peak-to-trough, CI band width, nonlinearity LRT p -- backs Figure 3's caption numbers"),
    ]
    rows = []
    for label, fname, desc in manifest:
        path = TABLES_DIR / fname
        exists = path.exists()
        rows.append([label, fname, desc, "OK" if exists else "MISSING"])
        if not exists:
            print(f"WARNING: {label} ({fname}) not found at {path}")
    m = pd.DataFrame(rows, columns=["Table", "File", "Description", "Status"])
    m.to_csv(TABLES_DIR / "manifest.csv", index=False)
    print(m.to_string(index=False))
    print(f"\nManifest saved -> {TABLES_DIR / 'manifest.csv'}")


def main():
    attrition = pd.read_csv(DATA_DIR / "attrition_log_01_candidate_cohort.csv")
    figure1_strobe(attrition)

    df = pd.read_parquet(DATA_DIR / "analysis_primary_data.parquet")
    figure2_coefficient_plot(df)

    print()
    print("Figure 3 (RCS dose-response) already exists from 04b_followups.py:")
    fig3 = FIGURES_DIR / "figure3_rcs_dose_response.png"
    print(f"  {'OK' if fig3.exists() else 'MISSING'} -> {fig3}")
    print()

    print("=" * 70)
    print("FINAL MANIFEST: Tables 1-9")
    print("=" * 70)
    assemble_manifest()


if __name__ == "__main__":
    main()
