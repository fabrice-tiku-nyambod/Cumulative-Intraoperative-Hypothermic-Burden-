"""
Parses pubmed-Hypothermi-set.nbib (a real PubMed search export) and ranks
records by relevance to this paper's actual topic (intraoperative
hypothermia, coagulation/bleeding, transfusion, perioperative AKI/outcomes)
to select a high-yield reference set.

Deliberately does NOT touch the other .nbib files in this directory tree
(frailtyTit-set.nbib, atrialfibr-set.nbib, CARDIAC REHABILITATION AND
WEARABLES.nbib, HERAT RATE RECOVERY.nbib, sixminutew-set.nbib) -- those are
from an unrelated project (frailty/exercise capacity) and citing them here
would be incoherent regardless of keyword overlap.
"""
import re
from pathlib import Path

import pandas as pd

NBIB_PATH = Path(r"c:\Users\tikuf\Desktop\vitaldb\pubmed-Hypothermi-set.nbib")
PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_PATH = PROJECT_DIR / "outputs" / "tables" / "references_ranked.csv"

RELEVANCE_TERMS = {
    "hypotherm": 3, "core temperature": 3, "core temp": 3, "normothermi": 2,
    "coagulat": 3, "coagulopathy": 3, "clotting": 2, "hemostas": 2, "haemostas": 2,
    "platelet": 2, "fibrinogen": 2, "aptt": 1, "prothrombin": 1, "pt-inr": 1,
    "blood loss": 3, "bleeding": 3, "hemorrhage": 2, "haemorrhage": 2,
    "transfusion": 3, "allogen": 1, "packed red": 1, "rbc transfusion": 2,
    "intraoperative": 2, "perioperative": 2, "surgical": 1, "surgery": 1,
    "anesthesia": 1, "anaesthesia": 1,
    "acute kidney injury": 2, "aki": 1, "creatinine": 1, "renal": 1,
    "warming": 2, "forced-air": 1, "thermoregulat": 2,
    "length of stay": 1, "mortality": 1, "outcome": 1,
}


def parse_nbib(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    raw_records = re.split(r"\n\s*\n(?=PMID-)", text.strip())
    records = []
    for raw in raw_records:
        lines = raw.split("\n")
        fields = {}
        current_tag, current_val = None, []
        for line in lines:
            m = re.match(r"^([A-Z]{2,4})\s*-\s?(.*)$", line)
            if m:
                if current_tag:
                    fields.setdefault(current_tag, []).append(" ".join(current_val).strip())
                current_tag, current_val = m.group(1), [m.group(2)]
            elif current_tag and line.startswith(("      ", "\t")):
                current_val.append(line.strip())
        if current_tag:
            fields.setdefault(current_tag, []).append(" ".join(current_val).strip())

        pmid = fields.get("PMID", [""])[0]
        title = fields.get("TI", [""])[0]
        abstract = " ".join(fields.get("AB", []))
        journal_full = fields.get("JT", [""])[0]
        journal_abbrev = fields.get("TA", [""])[0]
        year_match = re.search(r"\b(19|20)\d{2}\b", fields.get("DP", [""])[0])
        year = year_match.group(0) if year_match else ""
        authors = fields.get("FAU", [])
        first_author = authors[0] if authors else ""
        pub_types = fields.get("PT", [])
        volume = fields.get("VI", [""])[0]
        issue = fields.get("IP", [""])[0]
        pages = fields.get("PG", [""])[0]
        doi = ""
        for lid in fields.get("LID", []):
            m = re.search(r"([\d.]+/\S+)\s*\[doi\]", lid)
            if m:
                doi = m.group(1)

        if pmid and title:
            records.append({
                "pmid": pmid, "title": title.rstrip("."), "abstract": abstract,
                "journal": journal_full, "journal_abbrev": journal_abbrev, "year": year,
                "first_author": first_author, "all_authors": "; ".join(authors),
                "n_authors": len(authors), "pub_types": "; ".join(pub_types),
                "volume": volume, "issue": issue, "pages": pages, "doi": doi,
            })
    return records


def score_record(rec):
    text = (rec["title"] + " " + rec["abstract"]).lower()
    score = sum(weight for term, weight in RELEVANCE_TERMS.items() if term in text)
    # small bonus for review/clinical-trial/meta-analysis pub types (more citable for background claims)
    if any(pt in rec["pub_types"] for pt in ["Review", "Meta-Analysis", "Randomized Controlled Trial", "Clinical Trial"]):
        score += 2
    return score


def format_annals_of_surgery(rec, num):
    """Annals of Surgery (LWW) numbered reference style: first 3 authors then
    'et al' (not AMA's 6-author cutoff), no periods between author initials,
    journal abbreviation, Year;Volume(Issue):Pages."""
    authors = rec["all_authors"].split("; ") if rec["all_authors"] else [rec["first_author"]]
    if len(authors) > 3:
        author_str = ", ".join(authors[:3]) + ", et al"
    else:
        author_str = ", ".join(authors)
    cite = f"{num}. {author_str}. {rec['title']}. {rec['journal_abbrev'] or rec['journal']}. {rec['year']}"
    if rec["volume"]:
        cite += f";{rec['volume']}"
        if rec["issue"]:
            cite += f"({rec['issue']})"
    if rec["pages"]:
        cite += f":{rec['pages']}"
    cite += "."
    return cite


def main():
    records = parse_nbib(NBIB_PATH)
    print(f"Parsed {len(records)} records from {NBIB_PATH.name}")

    for r in records:
        r["relevance_score"] = score_record(r)

    df = pd.DataFrame(records).sort_values("relevance_score", ascending=False)
    print(f"Score distribution: min={df['relevance_score'].min()}, "
          f"max={df['relevance_score'].max()}, median={df['relevance_score'].median()}")
    print(f"Records with score 0 (no relevance-term hits at all): {(df['relevance_score']==0).sum()}")

    df.to_csv(OUT_PATH, index=False)
    print(f"Full ranked list saved -> {OUT_PATH}")

    top25 = df.head(25)
    print()
    print("=== Top 25 by relevance score ===")
    for _, r in top25.iterrows():
        print(f"[{r['relevance_score']:>2}] {r['year']} | {r['first_author']} | {r['title'][:90]}")

    top25.to_csv(PROJECT_DIR / "outputs" / "tables" / "references_top25.csv", index=False)
    print(f"\nTop 25 saved -> outputs/tables/references_top25.csv")

    formatted = [format_annals_of_surgery(r, i + 1) for i, (_, r) in enumerate(top25.iterrows())]
    refs_path = PROJECT_DIR / "references_formatted.md"
    refs_path.write_text("# References (Annals of Surgery style, top 25 by relevance, from pubmed-Hypothermi-set.nbib)\n\n"
                          + "\n\n".join(formatted), encoding="utf-8")
    print(f"Formatted (Annals of Surgery style) reference list -> {refs_path}")


if __name__ == "__main__":
    main()
