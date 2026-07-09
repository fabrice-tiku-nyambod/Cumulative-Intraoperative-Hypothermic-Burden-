"""
Renders manuscript_draft.md into a formatted PDF (Annals of Surgery style:
numbered references, running head, standard section order) with the three
committed figures and key tables embedded, using reportlab (pure Python,
no native/system dependencies -- weasyprint was tried first and failed on
this Windows environment due to missing GTK/Pango libraries).

Not a general markdown-to-PDF converter -- handles exactly the constructs
used in manuscript_draft.md (##/### headers, **bold**, *italic*, `code`,
horizontal rules, bullet lists) plus manual insertion points for figures
and key tables at their referenced locations in the text.
"""
import re
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                 Spacer, Table, TableStyle)

PROJECT_DIR = Path(__file__).resolve().parent.parent
MD_PATH = PROJECT_DIR / "manuscript_draft.md"
FIGURES_DIR = PROJECT_DIR / "outputs" / "figures"
TABLES_DIR = PROJECT_DIR / "outputs" / "tables"
OUT_PATH = PROJECT_DIR / "VitalDB_Hypothermia_Manuscript.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14,
                           alignment=TA_JUSTIFY, spaceAfter=8))
styles.add(ParagraphStyle("H1", parent=styles["Heading1"], fontSize=14, spaceBefore=14, spaceAfter=8))
styles.add(ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, spaceBefore=12, spaceAfter=6))
styles.add(ParagraphStyle("H3", parent=styles["Heading3"], fontSize=10.5, spaceBefore=10, spaceAfter=4))
styles.add(ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=16, leading=20, spaceAfter=6))
styles.add(ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, alignment=TA_CENTER,
                           textColor=colors.HexColor("#444444"), spaceAfter=4))
styles.add(ParagraphStyle("Ref", parent=styles["Normal"], fontSize=8.5, leading=11, spaceAfter=5))
styles.add(ParagraphStyle("Caption", parent=styles["Normal"], fontSize=9, leading=12,
                           textColor=colors.HexColor("#333333"), spaceAfter=12, spaceBefore=4))


def md_inline_to_reportlab(text):
    """**bold** -> <b>, *italic* -> <i>, `code` -> monospace font."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+?)`", r'<font face="Courier">\1</font>', text)
    return text


def load_csv_as_table(path, max_cols=6, font_size=6.5):
    df = pd.read_csv(path)
    if df.shape[1] > max_cols:
        df = df.iloc[:, :max_cols]
    data = [list(df.columns)] + df.astype(str).values.tolist()
    t = Table(data, hAlign="CENTER", repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef3fa")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def figure_flowable(fname, caption, max_width=6.3 * inch):
    img_path = FIGURES_DIR / fname
    img = Image(str(img_path))
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth = max_width
    img.drawHeight = max_width * ratio
    return [img, Paragraph(caption, styles["Caption"]), Spacer(1, 10)]


def build_story():
    text = MD_PATH.read_text(encoding="utf-8")
    # Body ends at the References section marker in the md (everything after
    # "## Notes for finalization" is drafting metadata, not manuscript content).
    text = text.split("## Notes for finalization")[0]
    lines = text.split("\n")

    story = []
    title_done = False
    in_refs = False
    para_buffer = []

    def flush_para():
        if para_buffer:
            joined = " ".join(para_buffer).strip()
            if joined:
                style = "Ref" if in_refs else "Body"
                story.append(Paragraph(md_inline_to_reportlab(joined), styles[style]))
            para_buffer.clear()

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if not title_done and line.startswith("# "):
            story.append(Paragraph(md_inline_to_reportlab(line[2:]), styles["TitleStyle"]))
            i += 1
            if i < len(lines) and lines[i].strip().startswith("*"):
                story.append(Paragraph(md_inline_to_reportlab(lines[i].strip()), styles["Sub"]))
                i += 1
            title_done = True
            story.append(Spacer(1, 10))
            continue

        if line.strip() == "---":
            flush_para()
            i += 1
            continue

        if line.startswith("## "):
            flush_para()
            heading = line[3:].strip()
            in_refs = heading.lower().startswith("references")
            if in_refs:
                story.append(PageBreak())
            story.append(Paragraph(md_inline_to_reportlab(heading), styles["H1"]))

            # Insert figures/tables at fixed anchor points right after their section heading.
            if heading.startswith("1. Introduction"):
                pass
            i += 1
            continue

        if line.startswith("### "):
            flush_para()
            story.append(Paragraph(md_inline_to_reportlab(line[4:].strip()), styles["H2"]))
            i += 1
            continue

        if line.strip().startswith("- "):
            flush_para()
            story.append(Paragraph("&bull; " + md_inline_to_reportlab(line.strip()[2:]), styles["Body"]))
            i += 1
            continue

        if in_refs and re.match(r"^\d+\.\s", line.strip()):
            flush_para()
            story.append(Paragraph(md_inline_to_reportlab(line.strip()), styles["Ref"]))
            i += 1
            continue

        if line.strip() == "":
            flush_para()
            i += 1
            continue

        para_buffer.append(line.strip())
        i += 1

    flush_para()
    return story


def insert_anchored_content(story):
    """Rebuild story inserting figures/key tables after specific paragraphs,
    identified by a distinctive substring of their text."""
    anchors = [
        ("2,567 cases were analyzed for Aims 1",
         lambda: figure_flowable("figure1_strobe.png",
             "<b>Figure 1.</b> STROBE cohort flow diagram: 6,388 total cases through "
             "candidate (N=2,824), analytic (N=2,568), and final Aim 1-3 (N=2,567) cohorts.")
         + [Paragraph("<b>Table 1.</b> Baseline characteristics by hypothermia-burden tertile.", styles["Caption"]),
            load_csv_as_table(TABLES_DIR / "table1_baseline_by_tertile.csv"), Spacer(1, 10)]),
        ("roughly a third higher odds of transfusion per clinically meaningful increase in exposure",
         lambda: figure_flowable("figure2_coefficient_plot.png",
             "<b>Figure 2.</b> Aim 1 primary model coefficients (SD-standardized), blood loss "
             "(linear) and transfusion (logistic).")),
        ("a real but small deviation from linearity that adds texture to",
         lambda: figure_flowable("figure3_rcs_dose_response.png",
             "<b>Figure 3.</b> Restricted cubic spline: hypothermia burden vs. predicted blood loss.")),
        ("nearly half the variance in directly measured blood loss accounts for almost none",
         lambda: [Paragraph("<b>Table 9.</b> Delta Hb vs. EBL, identical covariates/cohort/model type.", styles["Caption"]),
                  load_csv_as_table(TABLES_DIR / "table9_v1_replication_comparison.csv"), Spacer(1, 10)]),
        ("visible at a glance rather than requiring it to be reconstructed",
         lambda: figure_flowable("figure4_multi_outcome.png",
             "<b>Figure 4.</b> Hypothermia burden across all five tested outcomes: one confirmed "
             "finding (transfusion), one that fails multiplicity correction (LOS), three nulls "
             "(EBL, Delta Hb, AKI).")),
    ]

    new_story = []
    for flow in story:
        new_story.append(flow)
        if hasattr(flow, "text"):
            for marker, builder in anchors:
                if marker in flow.text:
                    result = builder()
                    if isinstance(result, list):
                        new_story.extend(result)
                    else:
                        new_story.append(result)
    return new_story


def main():
    story = build_story()
    story = insert_anchored_content(story)

    doc = SimpleDocTemplate(
        str(OUT_PATH), pagesize=letter,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.9 * inch, bottomMargin=0.9 * inch,
        title="Cumulative Intraoperative Hypothermic Burden Predicts Transfusion Practice but Not Measured Blood Loss",
        author="VitalDB Hypothermia Secondary Analysis",
    )
    doc.build(story)
    print(f"PDF written -> {OUT_PATH} ({OUT_PATH.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
