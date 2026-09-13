"""Generate gwr/utils/field_labels.py (DE/FR/IT) from ch/*_specifications.pdf.

Run: uv run python scripts/gen_field_labels.py

Column x-positions differ per PDF (each spec lays its table out at a different
absolute width), so column anchors (the left-edge x0 of each column) are
detected per document from its header rows instead of using fixed pixel
bands:
  - the row containing "Bezeichnung"/"Désignation"/"Designazione" together
    gives the DE/FR/IT column anchors,
  - separate stacked header rows containing "Nr."/"N°"/"No.",
    "Spez."/"Spec.", and "Abkürzung"/"Abréviation"/"Abbreviazione" give the
    Nr/Spez/Abbr anchors.
A word is then assigned to the column whose anchor is the largest one at or
before the word's x0 (with a small tolerance for float rounding). This
avoids the bug where a fixed cutoff (e.g. x0 < 302) misclassifies a column's
own anchor word when its true x0 (e.g. 301.74) sits a hair below the cutoff.
"""
import re
from pathlib import Path

import pdfplumber

SPECS = [
    "ch/gebaeude-batiment-edificio_specifications.pdf",
    "ch/eingang-entree-entrata_specifications.pdf",
    "ch/wohnung-logement-abitazione_specifications.pdf",
]
OUT = Path("gwr/utils/field_labels.py")

NR_TOKENS = {"Nr.", "N°", "No."}
SPEZ_TOKENS = {"Spez.", "Spec."}
ABBR_TOKENS = {"Abkürzung", "Abréviation", "Abbreviazione"}
TOL = 0.5  # float-rounding tolerance for x0 comparisons

# Some date fields (e.g. GBAUJ, GBAUM) render an inline format hint ("YYYY", "MM") as the
# last word of the DE cell only (FR/IT don't repeat it). It's a single letter repeated, which
# no real German/French/Italian word is, so it's safe to strip as trailing noise.
_FORMAT_HINT_RE = re.compile(r"^([A-Za-z])\1+$")


def _strip_trailing_format_hint(words):
    if words and _FORMAT_HINT_RE.match(words[-1]):
        return words[:-1]
    return words


def _detect_anchors(pdf):
    """Find the left-edge x0 of each column (Nr/DE/FR/IT/Spez/Abbr) for this document."""
    nr_x = spez_x = abbr_x = None
    de_x = fr_x = it_x = None
    for page in pdf.pages:
        rows = {}
        for w in page.extract_words(use_text_flow=False):
            rows.setdefault(round(w["top"], 1), []).append(w)
        for top in sorted(rows):
            texts = {w["text"]: w["x0"] for w in rows[top]}
            if "Bezeichnung" in texts and "Désignation" in texts and "Designazione" in texts:
                # this combined DE/FR/IT row is the last header row; data rows follow it, and
                # some data rows contain e.g. the IT word "Abbreviazione" as a translated label
                # (not the column header), so we must stop scanning before we reach them.
                de_x, fr_x, it_x = texts["Bezeichnung"], texts["Désignation"], texts["Designazione"]
                break
            for t in NR_TOKENS:
                if t in texts:
                    nr_x = texts[t] if nr_x is None else min(nr_x, texts[t])
            for t in SPEZ_TOKENS:
                if t in texts:
                    spez_x = texts[t] if spez_x is None else min(spez_x, texts[t])
            for t in ABBR_TOKENS:
                if t in texts:
                    abbr_x = texts[t] if abbr_x is None else min(abbr_x, texts[t])
        if None not in (nr_x, de_x, fr_x, it_x, spez_x, abbr_x):
            break  # anchors are stable for the whole document once found
    if None in (nr_x, de_x, fr_x, it_x, spez_x, abbr_x):
        raise RuntimeError("could not detect all column anchors from header rows")
    # (anchor_x, band_name) sorted left-to-right; the Nr and Spez columns map to None (skipped)
    return sorted([(nr_x, None), (de_x, "de"), (fr_x, "fr"), (it_x, "it"),
                   (spez_x, None), (abbr_x, "abbr")])


def _make_band(anchors):
    def band(x0):
        result = None
        for anchor_x, name in anchors:
            if x0 >= anchor_x - TOL:
                result = name
            else:
                break
        return result

    return band


def parse(path):
    out = {}
    with pdfplumber.open(path) as pdf:
        anchors = _detect_anchors(pdf)
        band = _make_band(anchors)
        for page in pdf.pages:
            rows = {}
            for w in page.extract_words(use_text_flow=False):
                rows.setdefault(round(w["top"], 1), []).append(w)
            for top in sorted(rows):
                cols = {"de": [], "fr": [], "it": [], "abbr": []}
                for w in sorted(rows[top], key=lambda w: w["x0"]):
                    b = band(w["x0"])
                    if b:
                        cols[b].append(w["text"])
                abbr = " ".join(cols["abbr"]).strip()
                # skip header rows / non-field rows: abbr must be a single UPPER token
                if not abbr or " " in abbr or not abbr.isupper():
                    continue
                out[abbr] = {
                    "de": " ".join(_strip_trailing_format_hint(cols["de"])).strip(),
                    "fr": " ".join(_strip_trailing_format_hint(cols["fr"])).strip(),
                    "it": " ".join(_strip_trailing_format_hint(cols["it"])).strip(),
                }
    return out


def main():
    labels = {}
    for s in SPECS:
        labels.update(parse(s))
    lines = ['"""Generated by scripts/gen_field_labels.py from ch/*_specifications.pdf. Do not edit by hand."""', ""]
    lines.append("FIELD_LABELS: dict[str, dict[str, str]] = {")
    for abbr in sorted(labels):
        d = labels[abbr]
        lines.append(f'    {abbr!r}: {{"de": {d["de"]!r}, "fr": {d["fr"]!r}, "it": {d["it"]!r}}},')
    lines.append("}")
    lines += ["", "", "def field_label(name: str, lang: str | None = None) -> str:",
              "    from django.utils.translation import get_language", "",
              "    lang = lang or get_language() or \"de\"",
              "    entry = FIELD_LABELS.get(name)",
              "    if not entry:", "        return name",
              "    return entry.get(lang) or entry.get(\"de\") or name", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT} with {len(labels)} fields")


if __name__ == "__main__":
    main()
