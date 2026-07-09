# Manuscript Proposal: Cumulative Intraoperative Hypothermic Burden Predicts Transfusion Practice but Not Measured Blood Loss — A Decision-Outcome / Physiologic-Outcome Divergence

**A secondary analysis of the VitalDB open-access perioperative database**
Draft protocol — v4 (reframed after §6d result — supersedes v3's "surrogate-sensitivity" framing, which the data did not confirm; see rationale below)

**Reframe rationale (v4, locked — this is a correction, not a repeat of the v3 exercise):** v3 predicted that burden would replicate as significant for ΔHb (matching v1) while staying null for EBL — that would have made "surrogate vs. direct outcome" the paper's throughline. §6d was run to test this directly, pre-specified as "a test, not a foregone conclusion." **It did not confirm:** burden is null for ΔHb too (p=0.360), not just EBL (p=0.418) — so there is no surrogate/direct discordance to report; the two blood-loss measures agree with each other (both null). Reporting v3's framing anyway would misrepresent what was actually found. The real, data-supported divergence sits elsewhere: burden significantly predicts the clinical *decision* to transfuse (OR≈1.33/SD) while predicting *none* of the three ways this dataset measures actual blood loss (EBL, ΔHb, or — implicitly — the R² collapse from 0.484 to 0.068 between the EBL and ΔHb models, meaning the covariate set that explains blood loss well barely explains ΔHb at all). That is the honest headline: a behavioral/practice outcome moves with burden; no physiologic measure of bleeding does. State the v3→v4 correction explicitly in the Introduction or a methods note — this is what pre-registering a test and reporting it honestly looks like, including when it fails.

---

## 1. PICO Framework

| Element | Specification |
|---|---|
| **Population** | Adults (≥18 y) undergoing major noncardiac surgery (general, thoracic, urological, gynecological) in VitalDB, operative duration >120 min, with continuous intraoperative core temperature tracking and complete covariate data |
| **Exposure (Index)** | Cumulative intraoperative hypothermia burden — time-weighted degree-minutes with core temperature <36.0°C (primary); minimum core temperature and early thermal drop velocity (comparator exposure metrics) |
| **Comparator** | Within-cohort dose-response (burden as a continuous variable, plus tertile/quartile groups); minimum-temperature and thermal-drop-velocity models as competing exposure specifications (nested model comparison, as in v1) |
| **Outcome** | **Primary:** intraoperative estimated blood loss and RBC transfusion requirement. **Secondary (mechanistic):** perioperative change in coagulation parameters (PT/INR, aPTT, fibrinogen). **Secondary (clinical/hard):** postoperative AKI (KDIGO creatinine criteria), postoperative and ICU length of stay, in-hospital mortality (descriptive only — see §7) |
| **Study Design** | Retrospective cohort, secondary analysis of open, de-identified data |

**Note on what changed from v1:** the prior draft used postoperative day-1 hemoglobin decline (ΔHb) as the sole outcome and explicitly cited unavailable transfusion data as a limitation. That data exists in VitalDB (`intraop_ebl`, `intraop_rbc`, `intraop_ffp`) and is used directly here. ΔHb is retained only as a sensitivity/secondary outcome for comparability with prior literature.

---

## 2. Specific Aims (framing updated to match the actual §6d result — see v4 rationale above; the underlying tests themselves are unchanged from what was prespecified and executed)

**Paper's actual contribution, stated plainly:** cumulative hypothermia burden shows a real, robust association with the decision to transfuse (Aim 1, OR≈1.33 per SD) but with none of the three ways this dataset measures actual blood loss — directly (EBL, p=0.418), by the standard literature surrogate (ΔHb, p=0.360), or via AKI/LOS as downstream physiologic consequences (Aim 3, null/uncorrected). §6d formally confirms this isn't an artifact of outcome choice: switching from EBL to ΔHb changes nothing about the conclusion (both null), which rules out "wrong outcome measure" as the explanation for the blood-loss null and instead points toward burden influencing transfusion *practice* through a channel other than measured hemorrhage. The burden-outcome relationship is also not uniform across surgical subtype (significant burden×stomach-surgery interaction, Aim 1), with the mechanism genuinely undetermined between effect modification and coverage-driven selection artifact. This is the paper: a clinical decision that tracks a physiologic exposure without any accompanying evidence of the physiologic harm the decision is nominally responding to — reported as a real, somewhat unresolved finding, not forced into a tidier story.

**§6d comparison (elevates §6's "ΔHb, sensitivity only" into a first-class, completed part of the paper):** fit the identical final Aim 1 model specification — same exposure, same covariates, same cohort (N=2,567) — against ΔHb as the outcome instead of `intraop_ebl`, reported side by side (coefficient, SE, 95% CI, p, R², N). **Run — see §6d for results.**



**Aim 1 (primary, confirmatory).** Determine whether cumulative intraoperative hypothermia burden is independently associated with intraoperative blood loss and RBC transfusion requirement, compared with minimum core temperature and thermal drop velocity as competing exposure metrics.

**Aim 2 (secondary, mechanistic).** Determine whether hypothermia burden is associated with perioperative derangement of coagulation parameters (PT/INR, aPTT, fibrinogen), testing the proposed causal pathway directly rather than inferring it from the literature.

**Aim 3 (secondary, clinical significance).** Determine whether hypothermia burden is associated with postoperative AKI (KDIGO creatinine criteria) and postoperative/ICU length of stay. In-hospital mortality will be reported descriptively only (see §7 — likely too rare for adjusted modeling in this cohort).

**Aim 4 — DEFERRED to a future paper (decision locked in §3b; not part of this manuscript).** Would have tested whether intraoperative hypotension burden (time-weighted degree-minutes with MAP <65 mmHg, derived from arterial waveform/numeric tracks) modifies or acts synergistically with hypothermia burden on AKI risk, extending the physiologic-burden framework established for hypotension alone (Salmasi et al., *Anesthesiology* 2017) to a second, less-studied intraoperative stressor.

All aims are framed as associative and hypothesis-generating; no causal or predictive-superiority language should be used in results/discussion, consistent with a retrospective single-center design.

---

## 3. Data Source

- **Database:** VitalDB v1.0.0, PhysioNet (DOI 10.13026/czw8-9p62)
- **Population:** 6,388 noncardiac surgery cases, Seoul National University Hospital, Aug 2016–Jun 2017
- **IRB:** Seoul National University Hospital H-1408-101-605; registered NCT02914444 (secondary analysis of de-identified open data — confirm your home institution's policy on whether this requires exempt/non-human-subjects determination before submission)
- **Files used:** `clinical_data.csv`, `lab_data.csv`, vital-sign waveform/numeric tracks (via `vitaldb` Python package), `clinical_parameters.csv` / `lab_parameters.csv` as data dictionaries

**Data verification checklist — VERIFIED against `DATASET/` directly (candidate cohort N = 2,865: age ≥18, department ∈ {General surgery, Thoracic, Urology, Gynecology}, (opend−opstart) > 120 min):**

- [x] `intraop_ebl`: 83.0% complete (2,378/2,865). `intraop_rbc`/`intraop_ffp`: 100% complete as numeric unit fields (0 = none given). Transfusion rate 10.2% (292/2,865) — adequately powered for logistic regression with the planned covariate set.
- [x] Postoperative creatinine: 2,487/2,865 (86.8%) have ≥1 draw within 48h; 2,506/2,865 (87.5%) within 7d. `preop_cr` baseline available for 2,718/2,865 (94.9%). **Aim 3 AKI analysis is well-powered — proceed as a primary secondary aim, not exploratory.**
- [x] Postoperative coagulation panel within 24h: `ptinr` 1,691/2,865 (59.0%), `aptt` 1,677/2,865 (58.5%), `fib` 1,672/2,865 (58.4%). Confirms the suspected non-routine yield. **Decision: Aim 2 is reframed as exploratory / complete-case-only**, regardless of the missingness-mechanism check below — see §6.
- [x] `death_inhosp` = 1: 24/2,865 (0.8%). Confirms the <10-events-per-covariate concern. **Mortality remains descriptive-only, no adjusted model.**
- [x] Reoperation clustering: 39 subjects contribute >1 case (41 extra cases). **Drop the 41 non-index cases**, retain first case per `subjectid`.
- [x] Cardiac-surgery exclusion criterion is moot — `department` has exactly 4 values in this cohort (General surgery, Thoracic, Urology, Gynecology); there is no cardiac surgery in VitalDB at all. Excludes zero cases; removed from §4 below.
- [x] Track access confirmed: `vitaldb.load_case()` reached the remote API successfully (0.37s single-track pull), and time-indexing at `interval=10` matches the `casestart=0` convention already confirmed for `clinical_data.csv`. 50-case benchmark: 50/50 succeeded, ~0.86 cases/sec (full N≈2,824 run ≈ 55 min).
- [x] **Coverage threshold revised** — a flat ≥80%-of-full-window rule only passed 29/50 (58%) and was shown to be duration-biased, not a genuine data-quality signal (see §4 for the trimmed-window/95%-interior replacement rule and the physiological reasoning re: redistribution hypothermia). Aim 4 (hypotension-burden interaction) remains viable — `Solar8000/ART_MBP` coverage should be checked with the same trimmed-window logic once `02_build_exposures.py` completes.
- [x] **Full-cohort run complete (N=2,824 candidates post-dedup): coverage rule confirmed and a real, non-random exclusion mechanism identified — now formally quantified and reproducible.** `is_stomach` predicts coverage failure. Unadjusted: **OR 6.62 (95% CI 4.84-9.05), Fisher's exact p=8.2×10⁻³²** (final reported test — Fisher's exact used over the earlier χ² approximation as the more defensible test for this table; note OR ≠ the earlier back-of-envelope rate ratio of ~5.5x — OR is expectedly more extreme than a simple proportion ratio at these prevalence levels, not a contradiction). Adjusted for duration, approach, and position: **OR 0.213 for passing coverage (i.e., ~4.7x higher odds of failing), p=9.6×10⁻¹²** — not explained by stomach surgery's skew toward videoscopic approach (77% vs 40%) or supine position (91% vs 53%). Plausible mechanism: intraoperative endoscopy/NG tube manipulation common in gastric procedures dislodging the esophageal probe, consistent with the large-contiguous-gap pattern (not scattered dropout) on trace inspection. Excluded cases also run longer (241 vs 218 min, p=0.002).
- [x] **Outcome-level bias check (the checkable half of "does exclusion distort things" — see §8 Table 8 scope note):** no differential attrition by `intraop_ebl`, overall (p=0.298) or within stomach cases specifically (p=0.735) — exclusion tracks `optype` and duration, not outcome severity. Reassuring for treating the exclusion as ignorable conditional on observed covariates, but does **not** establish that the burden→outcome relationship itself is the same in excluded cases (unmeasurable by construction) — state both facts, not just the reassuring one.
- [x] **`no_valid_bt` = 75** (corrected from an initial miscounted 73 — 2 cases were masked by transient network errors during the retry pass and only became visible once connectivity stopped being the confound; verified no retry-pass contamination via `status.str.startswith('error')` filter logic).
- [x] **Reproducibility:** extraction and bias-check logic are committed scripts, not ad hoc terminal output — `02_build_exposures.py`, `02b_coverage_bias_check.py`, output `outputs/tables/excluded_vs_included_comparison.csv`, git history `38c62a8 → 56dc9f1 → d9ada7a`. This is a genuine cohort-composition finding, not benchmark noise — reported formally (§8 Table 8) and in limitations (§10), not just as a footnote.

---

## 3b. Pre-Drafting / Pre-Task-3 Checklist (locked — resolve in order before proceeding)

**Before Introduction/Methods drafting:**
- [x] **Final analytic N confirmed directly from pipeline output** (`data/final_exposure_cohort.parquet`, filtered `status=='ok'` and `bt_coverage_trimmed >= 0.95`): **N = 2,568**. This is the number for Methods/Table 1 — not backed into.
- [x] **Aim 4 checked** (`Solar8000/ART_MBP`, same trimmed-window logic): 636/2,748 candidates (23.1%) have zero MAP data (no arterial line placed — consistent with the acuity/monitoring-intensity mechanism already identified for coag-panel yield). Of cases with any MAP data, 98.8% (2,087/2,112) clear the 95% threshold — MAP monitoring is essentially continuous once an a-line is placed, unlike BT. Combined BT-pass AND MAP-pass: **N = 1,951 (76.0% of the 2,568 analytic cohort)** — numerically viable, but a systematically non-random subset (arterial-line/high-acuity cases only), not a random 76%. **Decision: Aim 4 deferred to a future paper, not pursued in this manuscript** — Aims 1-3 aren't fully executed yet, and adding a systematically-biased fourth aim increases caveat burden without being necessary for a strong, focused, submittable result on this timeline. (Reversible — the cohort and coverage data are already extracted and cached if this decision changes.)

**Before `03_build_outcomes.py`:**
- [x] Field names verified against actual `lab_data['name'].value_counts()` (done during original protocol review, not new work): `hb`, `cr`, `ptinr`, `aptt`, `fib` all confirmed as literal string values. Bonus finding: `lab_data.csv` also contains a `p` (phosphorus, 16,440 rows) value absent from `lab_parameters.csv`'s dictionary — not a referenced field, doesn't affect §6, but further confirms the published dictionary is unreliable in both directions (lists fields that don't exist, and omits fields that do).
- [x] **KDIGO staging logic pinned:** anchor = `opend` (consistent with the LOS anchor decision; the `opend`-`aneend` gap is negligible against a 48h/7d window, so this is a narrative-consistency choice, not a numerically consequential one). Aggregation = peak creatinine within each window vs. baseline (standard convention — captures worst derangement, not whatever was drawn first). **Staging algorithm: the 48h delta (≥0.3 mg/dL) and 7d ratio (1.5-1.9x/2.0-2.9x/≥3.0x) criteria are evaluated independently and OR'd, taking the maximum stage triggered by either rule** — do not require both to fire. Baseline = `preop_cr` as given in `clinical_data.csv` (consistent with how `preop_hb` was already handled in the original draft; optional non-blocking sensitivity check against lowest `lab_data.csv` preop value if time permits, not required).
- [x] **Aim 2/Aim 3 completeness percentages recomputed at final N=2,568** (vs. original N=2,865 candidate cohort): essentially unchanged — coag yield 59.0-59.2%/58.4-58.6%/58.4%, creatinine 86.5-87.2%, preop_cr baseline 94.9%, transfusion rate 10.2% unchanged. **Mortality thinner: 17/2,568 (0.66%)**, down from 24/2,865 (0.84%) — reinforces descriptive-only framing, no change needed to any Aim 2/3 exploratory-vs-primary decisions.
- [x] Extend Table 8 to include AKI/coagulation comparison once those outcomes exist (sequenced after `03_build_outcomes.py` runs, not a blocker before starting it).

**Before Task #4 / Results:**
- [x] Execute everything specified but not yet run in §7: burden×optype interaction, 30-min early-gap sensitivity subset, VIF diagnostics, Holm-Bonferroni correction.

**Not blocking, resolve opportunistically:** exponential backoff on `api.vitaldb.net` calls; confirm the PhysioNet `vital_files/<caseid>.vital` static path with a real HTTP status check (both only matter for Aim 4 or a future rerun).

## 4. Cohort Selection

**Inclusion:**
- Age ≥18 years
- Noncardiac surgery: `department` ∈ {General surgery, Thoracic, Urology, Gynecology} — this is the full set of values present; no separate `optype` filter needed
- Operative duration >120 minutes, **derived** as `(opend − opstart) / 60`. **`opdur` is not a usable field in `clinical_data.csv` despite appearing in the published PhysioNet data dictionary — see note below.**
- Continuous core temperature track (Solar8000/BT): **revised coverage criterion (locked after 50-case benchmark, see §3).** A flat ≥80% of the full anesthesia window was tested and rejected — it is duration-biased (penalizes shorter, just-over-120-min cases) and conflates normal probe-placement/removal timing with genuine data dropout. Traced interior gaps were near-zero (0-265s out of 10,000+s windows); missingness is structural, concentrated at the start (median ~23 min, probe placed after induction) and end (median ~27 min, probe removed before emergence). **Revised rule:** trim each case's analysis window to `[first non-null BT reading, last non-null BT reading]`; require ≥95% coverage *within that trimmed window* (interior dropout should be rare given benchmark results, so this correctly flags genuine monitoring failures rather than normal instrumentation timing). Store the pre-monitoring gap length (`first_BT_reading − anestart`) per case for the sensitivity analysis in §7.
- Complete data for primary exposure and primary outcome variables (apply per-outcome, not as a single blanket filter — see §3 completeness figures, which differ substantially by outcome)

**Exclusion:**
- Missing `intraop_ebl` or transfusion fields
- Temperature track coverage <80% of case duration (pending verification)
- Reoperation within the same `subjectid`: **39 subjects, 41 extra cases confirmed in the candidate cohort — drop non-index cases**

**Candidate cohort as verified: N = 2,865** (age ≥18, department filter, duration >120 min), before per-outcome completeness filtering and before the 41-case reoperation drop. Report both the candidate N and each subsequent analytic N (which will differ by outcome — e.g., ~2,378 for the blood-loss model, ~1,672-1,691 for the exploratory coagulation models) in the STROBE diagram, broken out by reason, not pooled.

> **Field-name note (fix before writing `02_build_exposures.py`):** the PhysioNet-published `clinical_parameters.csv` data dictionary for this release lists `opdur`, `los_postop`, and `los_icu` as valid fields. Direct inspection of the actual `clinical_data.csv` shows `opdur` and `los_postop` are not present, and `los_icu` exists under the name `icu_days` instead (see §6). Treat the published dictionary as a guide, not ground truth — confirm every field referenced in this protocol against `df.columns.tolist()` on the actual file before using it in a script, not just these three.

---

## 5. Exposure Definitions

**Primary — Cumulative hypothermia burden (time-weighted, degree-minutes):**

```
burden = Σ max(0, 36.0 − T(t)) × Δt   for all t in [anestart, aneend]
```
computed from the Solar8000/BT track at native 10-second resolution (`Δt` = 10/60 min), summed over the anesthesia window. This is a strict upgrade from v1's simple duration-below-threshold — it captures both how long and how far below 36.0°C the patient was, analogous to the AUC-based "hypotension burden" metric established in the perioperative outcomes literature.

**Comparator exposures (retained from v1 for nested model comparison):**
- Minimum core temperature (raw and 2-minute median-smoothed, as in v1's sensitivity analysis)
- Early thermal drop velocity (max decline within 30 min of induction)
- Simple duration <36.0°C (retain for direct comparability with v1's published-style metric)

**Artifact filtering:** retain v1's approach — discard recorded temperatures <32.0°C or >41.0°C as technical artifacts.

**Aim 4 exposure (if pursued) — Hypotension burden:**
```
hypotension_burden = Σ max(0, 65 − MAP(t)) × Δt   for MAP(t) < 65 mmHg
```
from arterial line MAP track (Solar8000/ART_MBP or equivalent), same windowing convention.

---

## 6. Outcome Definitions

| Outcome | Field(s) | Definition |
|---|---|---|
| Blood loss (primary) | `intraop_ebl` | Continuous, mL; consider log-transformation given right skew |
| Transfusion requirement (primary) | `intraop_rbc` | Binary (any RBC transfusion) and continuous (units) as co-primary specifications |
| Coagulation derangement (Aim 2 — **exploratory**) | `ptinr`, `aptt`, `fib` (from `lab_data.csv`, long format) | Δ from last preoperative value to first postoperative value within 24h. **Verified yield: 58.4-59.0% (n≈1,672-1,691/2,865)** — write this up as exploratory/complete-case, not confirmatory, and report the yield percentage explicitly in the methods, not just in a limitations footnote |
| AKI (Aim 3 — **well-powered, primary secondary aim**) | `cr` (preop `preop_cr` vs. postop `cr` from `lab_data.csv`) | KDIGO serum-creatinine criteria only, staged as peak-in-window vs. baseline, 48h and 7d criteria evaluated independently and OR'd (max stage wins): Stage 1: ≥0.3 mg/dL increase within 48h OR 1.5–1.9× baseline within 7d; Stage 2: 2.0–2.9× baseline; Stage 3: ≥3.0× baseline or ≥4.0 mg/dL. **Urine-output criteria cannot be applied** — `intraop_uo` is a single intraoperative total, not a postoperative time series. Verified completeness at final N=2,568: baseline 94.9%, 48h follow-up 86.5%, 7d follow-up 87.2%. **Chronic-baseline correction (found during `03_build_outcomes.py`, real bug, fixed — implemented as a criterion modification, not a cohort exclusion):** the unconditional `preop_cr ≥ 4.0 mg/dL` absolute-value Stage 3 criterion misclassified chronic dialysis/ESRD patients (mean `preop_cr` 9.19 mg/dL, ratio ~0.97 — no actual rise) as acute Stage 3 AKI, accounting for 90 of 103 initially-flagged Stage 3 cases (87%). **Fix implemented: Stage 3 = ratio≥3.0× baseline OR (absolute `cr`≥4.0 mg/dL AND a concurrent ≥0.3 mg/dL rise from `preop_cr`)** — i.e., the absolute-value criterion is conditioned on a genuine rise rather than triggering unconditionally. This is a better fix than a blanket high-baseline exclusion would have been: it correctly discards the spurious chronic-dialysis cases while preserving genuine acute-on-chronic injury (33 of the original 90 "absolute-only" cases had both a high absolute value and a real ≥0.3 rise, and correctly remain Stage 3). Result: Stage 3 count 103 → 46 (13 via ratio, 33 via rise-confirmed absolute). **Write-up note for Task #6:** this is a modified KDIGO operationalization, not the literal published criteria — state the modification and its rationale explicitly in Methods, don't imply unmodified KDIGO was applied. **Residual limitation, not fixed by this change:** even a genuine ≥0.3 mg/dL rise in a patient with a 9+ mg/dL baseline can reflect ordinary dialysis-timing variability rather than a new acute insult — chronic dialysis patients remain fundamentally hard to stage via creatinine alone; worth a sentence in Discussion/Limitations if relevant. |
| LOS (Aim 3) | `dis − opend`, `icu_days` | **Postoperative LOS = `(dis − opend) / 86400` days (locked decision: anchored to surgical end, not `aneend`** — anesthesia-emergence timing is noisier and not the clinically conventional LOS anchor). `los_postop` does not exist as a field; `los_icu` does not exist under that name but ICU LOS is available directly as `icu_days` — reference that field name in `03_build_outcomes.py`, no derivation needed. Consider negative-binomial or log-linear model given expected right skew |
| Mortality (Aim 3, descriptive only) | `death_inhosp` | **Verified: 24/2,865 events (0.8%)** — well below the ≥10-events-per-covariate bar. Report as counts/proportions by exposure tertile only; do not fit an adjusted model |
| ΔHb (sensitivity only) | `preop_hb` vs. postop `hb` (from `lab_data.csv`) | Retained from v1 for comparability with prior literature, not a primary endpoint |

**Lab value extraction pattern (`hb`, `cr`, `ptinr`, `aptt`, `fib` — all postoperative lab values):** none of these exist as columns in `clinical_data.csv`. All live in `lab_data.csv`, long format (`caseid`, `dt`, `name`, `result`), with `dt` in seconds relative to `casestart = 0` (negative = preoperative). This is the same join pattern v1's ΔHb pipeline already used for `postop_hb` — generalize it into one reusable function rather than rewriting it per lab value:

```python
def get_lab_value(lab_df, caseid, lab_name, window_start_sec, window_end_sec, mode="first"):
    """Return first (or closest-to-window-start) lab value for a case within a time window."""
    rows = lab_df[(lab_df.caseid == caseid) & (lab_df.name == lab_name)
                  & (lab_df.dt >= window_start_sec) & (lab_df.dt <= window_end_sec)]
    if rows.empty:
        return None
    return rows.sort_values("dt").iloc[0]["result"] if mode == "first" else rows["result"].iloc[-1]
```
Apply this once per (caseid, lab_name, window) combination and cache the result — don't re-query `lab_data.csv` per outcome per script run; it's the largest file in the release and repeated scans are the likely first performance bottleneck in `03_build_outcomes.py`.

**Aim 2 missingness check — VERIFIED:**
- Exposure severity vs. coag-panel presence: no correlation. `min_core_temp` (33.45 vs 33.42°C, p=0.52) and hypothermia burden/duration (138.1 vs 138.9 min, p=0.83) are essentially identical between cases with and without a postop coag draw. **Missingness is not driven by exposure severity** — this rules out exposure-ascertainment confounding, i.e., burden itself is not what determines who gets tested.
- Monitoring intensity vs. coag-panel presence: strongly correlated. Arterial-line cases: 1,526/2,187 (69.8%) had a postop coag draw vs. 166/678 (24.5%) without an arterial line (χ² p≈4×10⁻⁹⁷). Coag ascertainment tracks case acuity/monitoring intensity, not hypothermia exposure.
- Net effect: good news for internal validity (exposure and ascertainment are independent), but the missing-at-random assumption still fails on acuity grounds, so Aim 2 stays exploratory as planned — this result doesn't change that decision, it just lets the limitations paragraph be precise instead of speculative.

---

## 6b. Aim 1 Results Log (from `04_analysis_primary.py`, commits `209603f`, `21b8555` — locked, pending 3 follow-ups below)

**Model-build fixes (methodological, not just bookkeeping):**
- `early_thermal_drop_velocity` (62% complete) **removed from the primary fully-adjusted spec** — including it alongside burden/min-temp forced N down to 1,276, nearly halving power for no benefit to the primary comparison. **Run as its own separate comparator model instead.**
- Nested LRT chain fixed: Model 4 was silently fit on a different N than Models 1-3, invalidating the likelihood-ratio comparison. Corrected to a common analytic sample across all nested models.
- Transfusion-model separation fix verified in two passes: merging two zero-event `optype` categories (Thyroid, Breast) together still produced a zero-event bucket; fixed by merging into an existing category with real events instead.

**Results (final Aim 1 cohort N=2,567):**
- Table 1: clean monotonic dose-gradient across burden tertiles (age, EBL, transfusion rate, crystalloid volume, stomach-`optype` representation) — descriptive face validity, not an adjusted result.
- **Linear model (log EBL, N=2,089): burden not significant (p=0.418).** Nested LRT confirms no improvement over baseline+min_temp (p=0.415). **v1's ΔHb-based finding does not clearly replicate using the direct blood-loss outcome — state this plainly, don't downplay it.**
- **Logistic model (transfusion, N=2,484): burden significant, OR=1.0028/unit, p=0.001.** Unit not yet clinically interpretable — **re-express as OR per meaningful increment (per 100 units, per SD, or top-vs-bottom tertile) before write-up.**
- RCS spline: significant nonlinearity for burden→EBL (p=0.011) despite the null linear term. **Plot the actual curve shape before describing this finding — the shape (threshold vs. U-shape vs. other) determines the interpretation.**
- **Burden × `is_stomach` interaction: significant (p=0.036).** Direct evidence the exposure-outcome relationship varies by surgery type among observable (retained) cases — strengthens rather than resolves the concern from the coverage-bias check. **Needs a stratified table (burden effect estimated separately for stomach vs. non-stomach) before Discussion characterizes it.**
- Early-gap sensitivity subset (N=1,598): burden's coefficient sign flips (+0.00017 full vs. -0.00043 subset), neither significant — consistent with an unstable/null linear signal, not a reversal of a real effect.
- Comparator model (thermal drop velocity, N=1,276): not significant (p=0.29).
- VIF: all <2.3, no multicollinearity concern.

**Three follow-ups — done, commit `f70ecac`:**
1. **Transfusion OR re-expressed:** per 100 units of burden, OR=1.320 (95% CI 1.113-1.566); per SD (≈103 units), OR=1.330 (95% CI 1.116-1.585) — a real, interpretable ~third-higher odds of transfusion. Top-vs-bottom tertile OR=1.635 but p=0.070 (not significant) — categorizing the continuous exposure costs power; if a tertile table is used, it needs a note explaining this isn't a contradiction of the continuous result.
2. **RCS curve plotted:** shallow dip-then-rise (~161→144→155 mL across the observed range), ~18mL peak-to-trough against a ~40-50mL-wide CI band throughout — nonlinearity is statistically real (p=0.011) but small relative to its own uncertainty, consistent with (not overturning) the null linear finding. **Reference profile for absolute mL values is the modal covariate combination (`optype=Stomach`, a lower-bleeding archetype)** — curve sits ~150mL vs. the cohort's ~500mL mean; not an error, but the figure caption must state the reference profile explicitly.
3. **Stratified burden effect — the finding requiring the most careful write-up.** Stomach (N=322): β=-0.00078, p=0.261. Non-Stomach (N=1,767): β=+0.00019, p=0.376. Opposite signs, neither stratum individually significant (each underpowered) — the sign flip itself, not a simple "stronger in one group," drives the significant interaction term. **Two explanations remain live and indistinguishable at this N: genuine effect modification by surgery type, or selection artifact from the retained 322 stomach cases being a non-random, coverage-selected subset of all stomach surgery (already tied to acuity/monitoring-intensity in the coverage-bias findings).** Discussion must present both explicitly rather than default to the more narratively satisfying one — the data cannot adjudicate between them, and saying so is the correct, not the weak, position.

## 6c. Aim 2/3 Results Log (from `03b`/`05_analysis_secondary.py`, commits `aa75fe3`, `4063aca`)

**Real bug caught and fixed, not just this script's problem:** `aki_any = aki_stage >= 1` silently evaluated `NaN >= 1` to `False` rather than missing, miscoding all 449 unstaged cases as confirmed "no AKI" — contaminating `outcomes.parquet` directly and the already-reported Table 8 AKI row (both the percentage and the chi2 test itself). A second instance of the same bug class was found in `03b`'s `add_cat()` helper. **Both fixed, full pipeline re-run `03→03b→04→05`; confirmed Aim 1 (`04`) untouched since it never used `aki_any`.** Corrected Table 8 AKI row: 9.6% (n=2,119) included vs. 10.0% (n=219) excluded, p=0.937 (was wrongly 7.9%/8.6%/p=0.807) — the "no differential attrition" conclusion survives, but the reported numbers were wrong and needed correcting, not just the code. **Audit completed (see §9): one further dormant instance found in `02b`'s `add_cat()`, hardened defensively; all other flagged columns verified 100% complete.**

**Results, reported honestly (mostly do not confirm the hypothesized direction — this is a strength for credibility, not a weakness, and should be framed that way in Discussion, not softened):**
- **AKI (N=2,118):** burden not significant, OR=1.0002, p=0.794.
- **LOS (log-linear, N=2,482):** burden significant uncorrected at p=0.042, but **negative** — higher burden associated with *shorter* LOS, opposite the hypothesized direction.
- **Holm-Bonferroni (AKI+LOS, 2-test family):** LOS's p=0.042 tested first against threshold 0.025 — fails to reject. **Neither Aim 3 outcome survives family-wise correction.** Report LOS's direction/magnitude transparently but describe it as not surviving multiplicity correction, not as a causal finding.
- **ICU admission [supplementary, binary]:** not significant, p=0.163.
- **Coagulation [Aim 2, exploratory, uncorrected]:** PT-INR null (p=0.61). aPTT significant (p=0.0013) but counterintuitive direction (higher burden → shorter aPTT). Fibrinogen significant (p<0.0001), also counterintuitive (higher burden → fibrinogen rises more).
- **Mortality:** 4/6/7 deaths across burden tertiles, descriptive only as planned (17 total events).

**Candidate unifying explanation for Discussion (proposed, not confirmed):** burden accrues over time by construction, so it is structurally correlated with surgical duration/complexity. Since fibrinogen is a classic acute-phase reactant and surgical stress independently induces a transient hypercoagulable state (shortened aPTT, elevated fibrinogen) distinct from hypothermia-mediated coagulopathy, a **residual surgical-stress signal not fully captured by the duration covariate** is a coherent thread touching the LOS, aPTT, and fibrinogen reversals together. State as a candidate explanation only — duration is already adjusted for in these models, so this claims *residual*, unmeasured stress, which this data cannot directly confirm.

**Overall Aim 1-3 synthesis:** the single robust, hypothesis-consistent finding across the paper is burden→transfusion (Aim 1, ~32% higher odds per SD, survives as the most defensible result). Everything else is either null (EBL, AKI) or counterintuitive-and-uncorrected (LOS, coagulation) with a plausible confounding explanation. This mixed, honestly-reported pattern is more credible to a sophisticated reviewer than a clean confirmation across every outcome would have been — consistent with this paper's hypothesis-generating framing from the start.

## 6d. ΔHb-vs-EBL Comparison (Table 9 — run, does not confirm the v3 hypothesis, and that is itself the finding)

Fit the exact final Aim 1 EBL model specification (§6b — burden + min_temp + thermal drop velocity comparator, age, sex, BMI, ASA [ASA=6 excluded], emergency status, `optype` [collapsed-category version for any logistic use, full granularity for linear], operative duration, crystalloid/colloid volume, vasopressor use — `ane_type` excluded per the locked fix) against `ΔHb = preop_hb − postop_hb` as the outcome instead of log-`intraop_ebl`, on the identical N=2,567 cohort.

**Result:** burden is **not** significant for ΔHb (p=0.360), matching the EBL null (p=0.418). v1's original ΔHb finding (β≈0.0027/min) does not replicate even on its own outcome scale once the current covariate set/rigor is applied — so this is not "EBL and ΔHb disagree," it's "neither shows a burden effect once you adjust properly." The two models' R² also diverges sharply: **0.484 (EBL) vs. 0.068 (ΔHb)** — the same covariates that explain nearly half the variance in direct blood loss explain almost none of the variance in ΔHb, consistent with ΔHb being a noisier, more indirect proxy (confounded by fluid administration timing, hemodilution, and postop draw timing) rather than burden's effect simply being harder to detect on that scale.

**What this changes vs. the v3 plan:** v3 was written expecting this table to show discordance (ΔHb significant, EBL null) and built the paper's headline around that. It shows concordance instead — neither blood-loss measure moves with burden. The v3 "surrogate-sensitivity" framing is retired; see the v4 rationale at the top of this document for the corrected framing (transfusion-practice vs. physiologic-blood-loss divergence). **This section is closed — commit tagged in `RESULTS_PROVENANCE.md`.**

## 7. Statistical Analysis Plan

1. **Descriptive statistics** — Table 1, baseline characteristics by exposure tertile, as in v1.
2. **Primary models (Aim 1)** — multivariable linear regression (log-transformed `intraop_ebl`) and logistic regression (transfusion, binary), adjusting for age, sex, BMI, ASA class, emergency status, `optype`, operative duration, intraoperative crystalloid/colloid volume, and vasopressor use. Report burden alongside minimum temperature and thermal drop velocity in the same fully adjusted model, as in v1's Table 2. **`anesthesia type` removed from the covariate list** (found during model-build: 2,567 General vs. 1 Spinal in this duration-filtered cohort — near-zero variance, nothing to adjust on, risks a near-singular design matrix column rather than a meaningful estimate). **Separation in the transfusion (logistic) model, fixed by collapsing rare `optype` categories:** Thyroid (0/87) and Breast (0/67) surgery had zero transfusion events, causing quasi-complete separation. No Python-3.13-compatible Firth logistic package exists in this environment (`firthlogist`/`logistf` both unsupported). **Fix: merge Thyroid and Breast into an "Other/low-volume" `optype` bucket for the transfusion (logistic) model only — the EBL/linear model is unaffected and retains full `optype` granularity.** Rejected alternatives: a hand-written Firth implementation (unvalidated custom statistical code, materially higher and harder-to-detect risk than the covariate-collapsing fix, given real bugs already caught elsewhere in this pipeline via obviously-wrong output — a subtly wrong custom penalized-likelihood implementation would not have that same tripwire); a second Python 3.10 environment just for this model (technically correct but disproportionate ongoing reproducibility overhead for a covariate, not the exposure of interest). Confirm after merging that the combined bucket has nonzero events and that no other `optype` category has an undetected zero-event cell.

**One ASA=6 case (declared brain-dead organ donor) excluded from Aims 1-3** (N=2,568→2,567) — a construct-validity exclusion, not an outlier-statistics one: organ procurement from a brain-dead donor doesn't involve the living surgical stress response the study is modeling, regardless of clearing the department/duration filters. Document both as one-line Methods deviations.
3. **Nested model comparison** — replicate v1's Model 1→4 hierarchical structure (baseline → +minimum temp → +burden → full), reporting ΔR², AIC, BIC, and LRT p-value from one single, version-locked analysis script (see §9 — this was the main defect in the v1 drafts).
4. **Dose-response** — restricted cubic spline for burden vs. each primary/secondary continuous outcome, knots at 5th/35th/65th/95th percentiles (Harrell), nonlinearity tested by LRT against the linear specification, as in v1.
5. **Aim 2/3 models** — logistic regression for AKI (binary, staged as ordinal secondary specification), linear/negative-binomial for LOS. Apply a prespecified multiplicity correction (Holm-Bonferroni) across the Aim 2/3 secondary outcome family to control type I error, since several secondary endpoints are being tested.
6. **Aim 4 (if pursued)** — burden × hypotension-burden interaction term in the AKI model; report both main effects and the interaction with its own LRT.
7. **Diagnostics** — VIF (threshold ≥5) on all linear main-effects specifications, as in v1; sensitivity analysis using smoothed vs. raw temperature nadir.
7a2. **Burden × surgery-type interaction (added after the stomach-surgery coverage-failure finding, §3):** add a `hypothermia_burden × is_stomach` interaction term to the Aim 1 primary model. This cannot resolve whether the burden-outcome relationship differs in the *excluded* stomach cases (unmeasurable by construction), but it does test whether it differs among the *retained* stomach-surgery cases (the 457 that passed coverage) versus everyone else — a partial but genuine heterogeneity check, not a full answer. Report as its own line, not folded into the main effect.

7b. **Early-monitoring-gap sensitivity analysis (prespecified, added after the coverage-threshold revision in §4):** refit the Aim 1 primary model restricted to cases where BT monitoring began within 30 minutes of anesthesia start (`first_BT_reading − anestart ≤ 30 min`), the subset least likely to have missed the redistribution-hypothermia phase. Compare effect estimates against the full trimmed-window cohort. Report both the proportion of the cohort with a >30 min pre-monitoring gap and whether estimates are consistent across the two specifications — this is the direct empirical check on whether early-window missingness materially biases the burden metric, rather than relying on the redistribution-hypothermia literature alone.

**Verified on 50-case benchmark (confirms this is a real, non-redundant comparison, not a formality):** pre-monitoring gap mean 1,899s (~32 min), median 1,600s (~27 min), range 430s-7,200s. Only 58% (29/50) fall within the 30-min cutoff — the early-coverage subset is materially smaller than the full analytic cohort, not a near-duplicate of it. Design and report this comparison as a substantive robustness check, not a pro forma sensitivity line.
8. **Missing data** — report missingness by variable; primary analysis complete-case, sensitivity analysis via multiple imputation if missingness on key covariates exceeds 10%.
9. Software: Python 3, `pandas`, `numpy`, `statsmodels`, `scipy`, `patsy` (spline basis), `openpyxl` (write engine for §8 `.xlsx` tables), plotting via `matplotlib`/`seaborn`. **`lifelines` is not required** — LOS is modeled as a continuous/count outcome (negative-binomial/log-linear GLM on `dis − opend`), not time-to-event. There's no meaningful censoring in this EMR-linked retrospective cohort, and the one plausible competing risk (in-hospital death) occurs too rarely (24/2,865, locked as descriptive-only in §6) to justify a competing-risks survival framework. Revisit only if the LOS specification changes.

---

## 8. Planned Tables and Figures

- **Table 1** — Baseline characteristics by hypothermia burden tertile
- **Table 2** — Fully adjusted regression, Aim 1 (blood loss, transfusion)
- **Table 2b** — Transfusion OR re-expressed (per 100 units, per SD, top-vs-bottom tertile)
- **Table 2c** — Burden effect stratified by Stomach vs. non-Stomach surgery
- **Table 3** — Nested model comparison (Aim 1), single locked run
- **Table 4** — Coagulation parameter models (Aim 2)
- **Table 5** — AKI and LOS models (Aim 3)
- **Table 5b** — Holm-Bonferroni correction (AKI+LOS 2-test family)
- **Table 6** — VIF collinearity diagnostics
- **Table 7** — Descriptive mortality by exposure tertile (not modeled)
- **Table 8** — Comparison of included vs. excluded candidate cases (coverage-threshold failures): `optype` (stomach surgery specifically), operative duration, approach, position, and outcome variables where available (`intraop_ebl`/transfusion, AKI/coag). Documents the confirmed differential-exclusion finding (§3) rather than leaving it as a limitations-only claim. **Scope note:** this table can show whether excluded cases differ in case-mix and outcome levels; it cannot show whether the exposure-outcome relationship itself would differ in excluded cases, since burden is undefined for them by construction — state this boundary explicitly rather than letting the table imply more than it establishes.
- **Table 9 (§6d) — the paper's central table, done:** ΔHb vs. EBL, identical model specification, side by side. Result: burden null for both (p=0.360 ΔHb, p=0.418 EBL); R² 0.068 vs. 0.484 — supports the v4 framing (transfusion practice moves with burden, no blood-loss measure does), not the v3 surrogate-sensitivity framing it was originally designed to test.
- **Figure 1** — STROBE flow diagram
- **Figure 2** — Coefficient plot, Aim 1 primary model
- **Figure 3** — Restricted cubic spline, burden vs. blood loss
- **Figure 4 (repurposed)** — the Aim 4 interaction plot originally planned for this slot is deferred along with Aim 4 itself (not part of this manuscript). In its place: a multi-outcome summary forest plot, burden's per-SD coefficient across all five tested outcomes (transfusion, EBL, ΔHb, AKI, LOS) on their own modeled scales, three-way classified as confirmed / nominally-significant-but-fails-correction / null — added after Task #6 because the paper's actual shape (one real finding against four-plus-one nulls) wasn't known until the results existed. Script: `07_tables_figures.py::figure4_multi_outcome`.

---

## 9. Reproducibility / Repository Structure

Lock this in before writing any results text — the single biggest issue with the prior draft was that the manuscript and methods documents reflected two different, unreconciled runs of the pipeline.

```
project/
  data/                # raw exports (not committed), data dictionaries
  scripts/
    01_extract_cohort.py
    02_build_exposures.py     # burden calculations
    02b_coverage_bias_check.py
    02c_aim4_cohort.py
    03_build_outcomes.py      # AKI staging, coag deltas, etc.
    03b_extend_comparison_table.py
    04_analysis_primary.py    # Aim 1 models
    04b_followups.py
    04c_v1_comparison.py      # Table 9
    05_analysis_secondary.py  # Aims 2-3
    07_tables_figures.py
  outputs/
    tables/
    figures/
  VitalDB_Hypothermia_Manuscript_Proposal.md   # this file
```

Run the full pipeline end-to-end from a single entry point before generating any table for the manuscript. Version-control every run (git tag or commit hash referenced in a `RESULTS_PROVENANCE.md`) so you always know which commit produced which number — this directly prevents the Table 3 discrepancy from the v1 drafts.

**Pipeline status: locked, 1→7 complete (commit `74c6fdb`).** Full-codebase NaN-comparison-bug audit done across all 8 scripts (the bug class first found in AKI staging and `03b`'s `add_cat()` — see §6c): one further dormant instance found in `02b`'s `add_cat()`, not currently producing wrong output (every column it's called with is 100% complete) but hardened defensively since it's the same landmine. All other flagged columns (`transfused`, `sex`, `emop`, `optype`, `icu_days`, `intraop_eph`/`phe`/`epi`) verified 100% complete rather than assumed. The N=2,118 (Aim 3 AKI model) vs. n=2,119 (Table 8 "included" count) off-by-one is fully explained, not a residual bug: the ASA=6 organ-donor case is staged and counted in Table 8's broader cohort but excluded from the Aim 1-3 models specifically per the locked §7 exclusion. `07_tables_figures.py` complete: Figure 1 (STROBE, full 6,388→2,824→2,568→2,567 flow), Figure 2 (coefficient plot), Figure 3 (RCS spline), all 12 tables (1, 2, 2b, 2c, 3, 4, 5, 5b, 6, 7, 8, 9) confirmed present via `manifest.csv`. Everything is provenance-traced through `RESULTS_PROVENANCE.md`, from raw data to every number reported in this document. **No further pipeline or analysis work is pending.**

**Track extraction strategy (BT / ART_MBP, N ≈ 2,865 candidate cases) — locked decision:** use targeted `vitaldb.load_case(caseid, ['Solar8000/BT', 'Solar8000/ART_MBP'], interval=10)` calls against the remote API rather than bulk-downloading the full 95 GB release — you only need two named tracks per case, not the full case files. At this N, the remote API is still the slowest and most failure-prone part of the pipeline, so:
1. Benchmark on a random ~50-case batch first — record per-case latency and failure rate before committing to a full run.
2. Write each case's extracted track data to a local cache file (parquet/feather) immediately on success, keyed by `caseid`. Downstream steps (burden calculation, coverage check) should read from the cache, never re-hit the API.
3. Add retry/backoff and checkpointing (log completed `caseid`s to a file) so a network failure partway through doesn't force a restart from case 1.
4. Run the ≥80% coverage check (§3, §4) as part of this same extraction pass — you're already streaming the signal, so compute coverage while you're there rather than as a separate pass.

**Data source clarification (found during the full run — real distinction, not previously called out):** `vitaldb.load_case()` always hits VitalDB's own live server (`api.vitaldb.net`), not PhysioNet. PhysioNet separately hosts the raw per-case `.vital` files directly (`vital_files/` folder in the same v1.0.0 release, same access pattern as `clinical_data.csv` — wget/S3/individual HTTPS download), which can be read locally via `vitaldb.VitalFile(filepath, tnames)` without touching `api.vitaldb.net` at all. Likely URL pattern (fetched without error, but not confirmed via a real HTTP status check — verify with `requests.head()`/`curl -I` before relying on it): `https://physionet.org/files/vitaldb/1.0.0/vital_files/<caseid zero-padded to 5 digits>.vital`. If `api.vitaldb.net` shows rising, non-transient error rates (as happened during the full 2,824-case run — DNS resolution failures, not just occasional timeouts), prefer pulling the specific failed `caseid`s' `.vital` files from PhysioNet's static hosting for the retry pass rather than re-hitting the same live endpoint. **Add exponential backoff (e.g., 1s/2s/4s across 3 attempts) to any retry logic against `api.vitaldb.net` regardless** — immediate resubmission at the same rate against an endpoint that just showed transient failures is worse than a short backoff, and this is cheap to add before Aim 4's MAP-track extraction hits the same scale.

**Pipeline scope decision (locked):** `01_extract_cohort.py` handles tabular filtering only (age, department, derived duration, reoperation dedup) against `clinical_data.csv` — fast, deterministic, no network calls. It outputs a **candidate cohort** (STROBE attrition counts + `caseid` list + baseline fields). The ≥80% track-coverage exclusion happens in `02_build_exposures.py`, applied during the same pass that streams BT/ART_MBP for burden calculation, producing the **final analytic cohort**. Table 1 and the STROBE diagram reference the final cohort out of `02`, not the candidate count out of `01` — don't conflate the two when reporting N.

---

## 10. Anticipated Limitations (pre-register these — don't discover them at revision)

- Single-center, single-country (Korea) cohort — generalizability
- Retrospective design — no causal inference
- AKI staged by creatinine only, no urine-output criteria available
- Mortality likely too rare in a general noncardiac cohort for adjusted modeling
- Coagulation panel ascertainment (59% yield) was strongly associated with arterial line placement, a monitoring-intensity/acuity proxy (69.8% vs. 24.5%, χ² p≈4×10⁻⁹⁷), but not with hypothermia exposure severity (p=0.52-0.83). Missingness is therefore plausibly non-random with respect to case acuity, even though it is unrelated to the exposure of interest — Aim 2 findings should be interpreted as exploratory and complete-case only, not generalizable to lower-acuity cases without arterial monitoring
- Temperature-monitoring completeness is not uniform across the surgical case-mix: stomach surgery cases fail the coverage threshold at ~4.7x the adjusted odds of other surgery types (p=9.6×10⁻¹²), independent of duration, approach, and position, plausibly due to intraoperative endoscopy/NG tube manipulation dislodging the esophageal probe. Gastric procedures are therefore specifically underrepresented in the final analytic cohort relative to the candidate cohort — findings should not be assumed to generalize to gastric surgery without explicit caveat, and this exclusion pattern is quantified in Table 8, not merely asserted
- Effect sizes may again be small in absolute terms even where statistically significant; report clinical magnitude alongside p-values throughout, as v1 did well

---

## 11. Realistic Target Journals

Anesthesiology, British Journal of Anaesthesia, Anesthesia & Analgesia, Journal of Clinical Anesthesia, or Annals of Surgery if the AKI/hard-outcome story is strong enough. Not a top-5 general medicine journal — single-center secondary analyses don't clear that bar regardless of design quality — but this tier is a genuine, strong outcome for a residency/PhD-track publication.
