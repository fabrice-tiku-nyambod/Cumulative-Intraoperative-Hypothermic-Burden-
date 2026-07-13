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
MILESTONE_FILL = "#eef3fa"
DATAQUAL_COLOR = "#5b7c99"      # coverage/data-quality exclusions (most steps)
CONSTRUCT_COLOR = "#8e44ad"      # construct-validity exclusion (ASA=6) -- categorically different reason
LINE_COLOR = "#1f5fa8"           # hypothermia burden
TEMP_COLOR = "#2a9d8f"           # minimum core temperature (distinct hue from burden)
SIG_COLOR = "#c0392b"            # confirmed significant finding -- "hot"
NOMINAL_COLOR = "#c98a2c"        # nominally significant (raw p<0.05) but fails multiplicity correction
NULL_COLOR = "#9a9a9a"           # non-significant findings -- muted/gray
RUG_COLOR = "#888888"
CI_EDGE_COLOR = "#e8a33d"        # warm accent, separates "uncertainty" from "estimate"
EXPLORATORY_COLOR = "#6a4c93"    # distinct from SIG/NOMINAL/NULL -- exploratory outcomes were never
                                  # put through multiplicity correction at all, unlike LOS (which was
                                  # corrected and failed), so reusing NOMINAL_COLOR would misleadingly
                                  # imply the same "tested and failed" story


def _rounded_box(ax, xy, w, h, fc, ec, lw, zorder=2, pad=0.02):
    from matplotlib.patches import FancyBboxPatch
    box = FancyBboxPatch(xy, w, h, boxstyle=f"round,pad={pad},rounding_size=0.09",
                          facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder,
                          mutation_aspect=1)
    ax.add_patch(box)
    return box


def figure1_strobe(df_attrition):
    # Department is dropped as its own filtering step -- it excludes zero cases
    # (VitalDB's noncardiac cohort already sits entirely within these 4
    # departments), so it's stated as a cohort-definition fact folded into the
    # first box rather than a pointless "0 excluded" arrow with nothing on it.
    steps = [
        ("Noncardiac surgical cases\n(General/Thoracic/Urology/Gynecology)\nVitalDB v1.0.0", 6388, None, None),
        ("Age ≥ 18 years", 6323, "65 excluded\n(8 unparseable/missing age)", "data"),
        ("Operative duration\n(opend−opstart) > 120 min", 2865, "3,458 excluded", "data"),
        ("Reoperation dedup\n(index case per subjectid)", 2824, "41 excluded\n(39 subjects had >1 case)", "data"),
        ("CANDIDATE COHORT", 2824, None, None),
        ("BT trimmed coverage ≥ 95%\n(per-case observed-window rule)", 2568,
         "256 excluded:\n75 no_valid_bt\n1 empty-window\n180 failed coverage", "data"),
        ("ANALYTIC COHORT", 2568, None, None),
        ("Exclude ASA=6\n(brain-dead organ donor)", 2567,
         "1 excluded\n(physiologically non-comparable\nto surgical cohort)", "construct"),
        ("FINAL AIM 1-3 COHORT", 2567, None, None),
    ]

    box_w, box_h, gap = 5.6, 1.05, 0.55
    excl_w = 3.3
    box_x0 = 0.3
    excl_x0 = box_x0 + box_w + 0.75
    canvas_w = excl_x0 + excl_w + 0.3   # right margin so exclusion boxes are never clipped
    n_steps = len(steps)
    canvas_h = n_steps * box_h + (n_steps - 1) * gap + 1.3
    fig, ax = plt.subplots(figsize=(canvas_w, canvas_h * 0.82), dpi=600)
    ax.set_xlim(0, canvas_w)
    ax.set_ylim(0, canvas_h)
    ax.axis("off")
    y = canvas_h - 0.9
    for i, (label, n, excl_note, excl_kind) in enumerate(steps):
        is_milestone = label.isupper()
        fc = MILESTONE_FILL if is_milestone else "white"
        ec = BOX_EDGE if not is_milestone else "#3a5a80"
        lw = 2.2 if is_milestone else 1.1
        _rounded_box(ax, (box_x0, y - box_h), box_w, box_h, fc, ec, lw, zorder=2)

        cy = y - box_h / 2
        if is_milestone:
            ax.text(box_x0 + box_w / 2, cy + 0.16, label, ha="center", va="center",
                     fontsize=11, fontweight="bold", color="#1a3a5c", zorder=3)
            ax.text(box_x0 + box_w / 2, cy - 0.24, f"N = {n:,}", ha="center", va="center",
                     fontsize=13, fontweight="bold", color="#1a3a5c", zorder=3)
        else:
            ax.text(box_x0 + box_w / 2, cy + 0.15, label, ha="center", va="center",
                     fontsize=9, color=TEXT_COLOR, zorder=3, linespacing=1.4)
            ax.text(box_x0 + box_w / 2, cy - 0.32, f"N = {n:,}", ha="center", va="center",
                     fontsize=10.5, fontweight="bold", color=TEXT_COLOR, zorder=3)

        if excl_note:
            excl_color = CONSTRUCT_COLOR if excl_kind == "construct" else DATAQUAL_COLOR
            excl_fill = "#f5eefa" if excl_kind == "construct" else "#eef2f6"
            n_lines = excl_note.count("\n") + 1
            eh = 0.34 + 0.28 * n_lines
            ex0 = box_x0 + box_w + 0.75
            ey_top = cy + eh / 2
            # real arrow from the box edge to the exclusion callout, not a bare line
            ax.annotate("", xy=(ex0 - 0.04, cy), xytext=(box_x0 + box_w + 0.06, cy),
                         arrowprops=dict(arrowstyle="-|>", color=excl_color, lw=1.3, mutation_scale=12), zorder=1)
            _rounded_box(ax, (ex0, cy - eh / 2), excl_w, eh, excl_fill, excl_color, 1.1, zorder=2, pad=0.015)
            ax.text(ex0 + excl_w / 2, cy, excl_note, ha="center", va="center",
                     fontsize=7.6, color=excl_color, zorder=3, linespacing=1.5)

        if i < n_steps - 1:
            ax.annotate("", xy=(box_x0 + box_w / 2, y - box_h - gap + 0.08),
                         xytext=(box_x0 + box_w / 2, y - box_h - 0.03),
                         arrowprops=dict(arrowstyle="-|>", color=BOX_EDGE, lw=1.5, mutation_scale=14), zorder=1)
        y -= box_h + gap

    ax.plot([], [], color=DATAQUAL_COLOR, lw=2, label="Coverage / data-quality exclusion")
    ax.plot([], [], color=CONSTRUCT_COLOR, lw=2, label="Construct-validity exclusion")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 0.02), fontsize=8.5, frameon=False, ncol=2)

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

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), dpi=600)

    # Color encodes which variable (burden vs. min-temp); saturation/fill encodes
    # significance -- the one real finding (transfusion x burden) reads as "hot"
    # against everything else, which is muted gray regardless of variable.
    var_color = {"hypothermia_burden": LINE_COLOR, "min_core_temp": TEMP_COLOR}

    ax = axes[0]
    terms = ["hypothermia_burden", "min_core_temp"]
    ys = np.arange(len(terms))[::-1]
    for y, term in zip(ys, terms):
        b = m_lin.params[term] * sds[term]
        ci = m_lin.conf_int().loc[term] * sds[term]
        sig = m_lin.pvalues[term] < 0.05
        c = var_color[term] if sig else NULL_COLOR
        ax.plot([ci[0], ci[1]], [y, y], color=c, lw=2, solid_capstyle="round")
        ax.plot(b, y, "o", color=c, markersize=8 if sig else 6,
                markerfacecolor=c if sig else "white", markeredgecolor=c, markeredgewidth=1.5, zorder=3)
    ax.axvline(0, color="#666666", lw=1.3, linestyle=(0, (4, 2)), zorder=0)
    ax.set_yticks(ys)
    ax.set_yticklabels([labels[t] for t in terms], fontsize=9)
    ax.set_xlabel("Beta, log(EBL+1) per SD", fontsize=9)
    ax.set_title("A. Blood loss (linear, N={}) -- null for both".format(int(m_lin.nobs)), fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)

    ax = axes[1]
    for y, term in zip(ys, terms):
        or_val = np.exp(m_log.params[term] * sds[term])
        ci = np.exp(m_log.conf_int().loc[term] * sds[term])
        sig = m_log.pvalues[term] < 0.05
        c = var_color[term] if sig else NULL_COLOR
        ax.plot([ci[0], ci[1]], [y, y], color=c, lw=2, solid_capstyle="round")
        ax.plot(or_val, y, "o", color=c, markersize=8 if sig else 6,
                markerfacecolor=c if sig else "white", markeredgecolor=c, markeredgewidth=1.5, zorder=3)
    ax.axvline(1, color="#666666", lw=1.3, linestyle=(0, (4, 2)), zorder=0)
    ax.set_xscale("log")
    xticks = [0.8, 0.9, 1.0, 1.2, 1.4, 1.6]
    ax.set_xticks(xticks)
    ax.set_xticklabels([f"{t:g}" for t in xticks])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_yticks(ys)
    ax.set_yticklabels([labels[t] for t in terms], fontsize=9)
    ax.set_xlabel("Odds ratio, transfusion per SD", fontsize=9)
    ax.set_title("B. Transfusion (logistic, N={}) -- burden significant".format(int(m_log.nobs)), fontsize=10)
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


def figure5_coagulation_paradox(df):
    """The coagulation paradox (aPTT, fibrinogen -- both significant but in the
    counterintuitive direction, Aim 2, exploratory/uncorrected) given its own
    visual support rather than being left as prose + a table cell. Same style
    as Figure 2, but a distinct color (not SIG/NOMINAL/NULL from Figure 4) --
    these were never put through multiplicity correction at all, so coloring
    them like LOS ("tested and failed correction") would misstate what
    actually happened here."""
    f_aptt = f"delta_aptt ~ hypothermia_burden + min_core_temp + {COV_STR}"
    f_fib = f"delta_fib ~ hypothermia_burden + min_core_temp + {COV_STR}"
    sub_aptt = df.dropna(subset=["delta_aptt"])
    sub_fib = df.dropna(subset=["delta_fib"])
    m_aptt = smf.ols(f_aptt, data=sub_aptt).fit()
    m_fib = smf.ols(f_fib, data=sub_fib).fit()

    sd = df["hypothermia_burden"].std()

    fig, axes = plt.subplots(1, 2, figsize=(8, 3), dpi=600)

    for ax, m, label, unit in [(axes[0], m_aptt, "aPTT", "sec"), (axes[1], m_fib, "Fibrinogen", "mg/dL")]:
        b = m.params["hypothermia_burden"] * sd
        ci = m.conf_int().loc["hypothermia_burden"] * sd
        p = m.pvalues["hypothermia_burden"]
        ax.plot([ci[0], ci[1]], [0, 0], color=EXPLORATORY_COLOR, lw=2.5, solid_capstyle="round", zorder=2)
        ax.plot(b, 0, "o", color=EXPLORATORY_COLOR, markersize=10,
                markerfacecolor=EXPLORATORY_COLOR, markeredgecolor=EXPLORATORY_COLOR, zorder=3)
        ax.axvline(0, color="#666666", lw=1.3, linestyle=(0, (4, 2)), zorder=0)
        ax.set_yticks([])
        ax.set_ylim(-1, 1)
        ax.set_xlabel(f"Delta {label} per SD burden, {unit}", fontsize=9)
        p_label = "p<0.0001" if p < 0.0001 else f"p={p:.4f}"
        ax.set_title(f"{label} (N={int(m.nobs)}, {p_label})", fontsize=10)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(colors=TEXT_COLOR)
        ax.grid(axis="x", color="#e5e5e5", linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)

    fig.suptitle("Figure 5. The coagulation paradox: burden vs. aPTT/fibrinogen change\n"
                 "(Aim 2, EXPLORATORY -- uncorrected, not put through multiplicity correction)",
                 fontsize=10.5, color=TEXT_COLOR)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure5_coagulation_paradox.png", facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Figure 5 (coagulation paradox) saved -> {FIGURES_DIR / 'figure5_coagulation_paradox.png'}")


def figure4_multi_outcome(df):
    """The paper's argument in one image: burden's per-SD effect across all five
    outcomes, on each outcome's own natural modeled scale (log-OR for binary,
    beta for continuous -- not a manufactured common unit, since these outcomes
    have no shared natural scale, but each is a real fitted coefficient with a
    real CI). New figure -- fills the slot Aim 4 vacated when it was deferred.

    Significance coloring reflects the PAPER'S ACTUAL conclusions, not a flat
    p<0.05 cutoff: transfusion (p=0.001, Aim 1 primary, no correction issue) is
    the one true finding -> filled red. LOS (raw p=0.042) does NOT survive the
    Holm-Bonferroni correction already applied against AKI in Table 5b (fails
    at the 0.025 threshold) -- coloring it the same red as transfusion would
    visually contradict that table. LOS gets its own amber/half-open marker:
    "nominally significant uncorrected, does not survive correction" is a
    real third category here, not null and not confirmed."""
    sd = df["hypothermia_burden"].std()
    cov_logit = COV_STR.replace("C(optype)", "C(optype_collapsed)")

    specs = [
        ("Transfusion\n(log-OR/SD)", "transfused", cov_logit, "logit", None),
        ("EBL\n(log-beta/SD)", "log_ebl", COV_STR, "ols", None),
        ("Delta Hb\n(beta/SD, g/dL)", "delta_hb", COV_STR, "ols", None),
        ("AKI\n(log-OR/SD)", "aki_any", cov_logit, "logit", None),
        ("LOS\n(log-beta/SD)", None, COV_STR, "ols_los", None),
    ]

    rows = []
    for label, outcome, cov, kind, _ in specs:
        if kind == "ols_los":
            sub = df[df["los_postop_days"] > 0].copy()
            sub["log_los"] = np.log(sub["los_postop_days"])
            f = f"log_los ~ hypothermia_burden + min_core_temp + {cov}"
            m = smf.ols(f, data=sub).fit()
        elif kind == "logit":
            sub = df.dropna(subset=[outcome]) if outcome == "aki_any" else df
            f = f"{outcome} ~ hypothermia_burden + min_core_temp + {cov}"
            m = smf.logit(f, data=sub).fit(disp=0)
        else:
            f = f"{outcome} ~ hypothermia_burden + min_core_temp + {cov}"
            m = smf.ols(f, data=df).fit()
        b = m.params["hypothermia_burden"] * sd
        ci = m.conf_int().loc["hypothermia_burden"] * sd
        p = m.pvalues["hypothermia_burden"]
        rows.append([label, int(m.nobs), b, ci[0], ci[1], p])

    # Three-way classification matching the paper's actual conclusions, not a
    # flat p<0.05 cutoff: LOS is raw-p<0.05 but explicitly fails Holm-Bonferroni
    # in Table 5b, so it cannot be colored the same as transfusion's confirmed finding.
    def classify(label, p):
        if label.startswith("Transfusion"):
            return "confirmed" if p < 0.05 else "null"
        if label.startswith("LOS"):
            return "nominal" if p < 0.05 else "null"
        return "null"  # EBL, Delta Hb, AKI: none survive as findings regardless of p

    style = {
        "confirmed": dict(color=SIG_COLOR, markersize=10, fill=True),
        "nominal": dict(color=NOMINAL_COLOR, markersize=9, fill="half"),
        "null": dict(color=NULL_COLOR, markersize=7, fill=False),
    }

    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=600)
    ys = np.arange(len(rows))[::-1]
    for y, (label, n, b, lo, hi, p) in zip(ys, rows):
        cls = classify(label, p)
        s = style[cls]
        c = s["color"]
        ax.plot([lo, hi], [y, y], color=c, lw=2.2, solid_capstyle="round", zorder=2)
        if s["fill"] == "half":
            ax.plot(b, y, "o", color=c, markersize=s["markersize"],
                    markerfacecolor="white", markeredgecolor=c, markeredgewidth=2.2,
                    fillstyle="right", zorder=3)
        else:
            ax.plot(b, y, "o", color=c, markersize=s["markersize"],
                    markerfacecolor=c if s["fill"] else "white", markeredgecolor=c,
                    markeredgewidth=1.8, zorder=3)
        note = {"confirmed": " * significant", "nominal": " * raw p, fails correction", "null": ""}[cls]
        ax.text(hi + (0.02 * (max(r[4] for r in rows) - min(r[3] for r in rows))), y,
                f"p={p:.3f}{note}", va="center", fontsize=8, color=c)

    ax.axvline(0, color="#666666", lw=1.3, linestyle=(0, (4, 2)), zorder=0)
    ax.set_yticks(ys)
    ax.set_yticklabels([r[0] for r in rows], fontsize=9.5)
    ax.set_xlabel("Burden coefficient per SD (each outcome's own modeled scale -- see row labels)", fontsize=9)
    ax.set_title("Figure 4. Hypothermia burden across all five outcomes:\n"
                 "one confirmed finding (transfusion); LOS does not survive correction; three nulls",
                 fontsize=10.5, color=TEXT_COLOR)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(colors=TEXT_COLOR)
    ax.grid(axis="x", color="#e5e5e5", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)

    ax.plot([], [], "o", color=SIG_COLOR, markerfacecolor=SIG_COLOR, markersize=8, label="Confirmed (p<0.05)")
    ax.plot([], [], "o", color=NOMINAL_COLOR, markerfacecolor="white", markeredgecolor=NOMINAL_COLOR,
            markersize=7, markeredgewidth=2, label="Raw p<0.05, fails correction")
    ax.plot([], [], "o", color=NULL_COLOR, markerfacecolor="white", markeredgecolor=NULL_COLOR,
            markersize=7, markeredgewidth=1.8, label="Not significant")
    ax.legend(loc="lower right", fontsize=7.5, frameon=False)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure4_multi_outcome.png", facecolor="white", bbox_inches="tight")
    plt.close(fig)

    out = pd.DataFrame(rows, columns=["Outcome", "N", "Beta_per_SD", "CI_low", "CI_high", "p"])
    out.to_csv(TABLES_DIR / "figure4_multi_outcome_values.csv", index=False)
    print(f"Figure 4 (multi-outcome) saved -> {FIGURES_DIR / 'figure4_multi_outcome.png'}")
    print(out.to_string(index=False))


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
        ("Figure 4 values", "figure4_multi_outcome_values.csv", "Per-SD burden coefficient, CI, p for all 5 outcomes -- backs Figure 4's multi-outcome summary plot"),
        ("Table 2d", "table2d_preop_hb_sensitivity.csv", "Sensitivity analysis: Aim 1 models with preop_hb added -- transfusion association survives (OR/SD 1.330->1.320, still p<0.05), EBL remains null"),
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

    figure4_multi_outcome(df)
    print()

    figure5_coagulation_paradox(df)
    print()

    print("=" * 70)
    print("FINAL MANIFEST: Tables 1-9")
    print("=" * 70)
    assemble_manifest()


if __name__ == "__main__":
    main()
