import json
import re
import sys
from pathlib import Path

import pdfplumber

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PDF_PATH = DATA_DIR / "Document_for_processing.pdf"
OUTPUT_PATH = DATA_DIR / "segmented_statements.json"

FOOTER_RE = re.compile(r"^BibliotecadelCongresoNacionaldeChile\S*$", re.MULTILINE)
START_MARKER_RE = re.compile(r"CAP[IÍ]TULO\s+III\s*:")
END_MARKER_RE = re.compile(r"Anótese, tómese razón")

# Section/subsection headers within a chapter (e.g. "III.2 Transporte de
# Carga", "VI.6.2 Compensación de Emisiones..."), not institutional
# statements themselves -- left in place they'd otherwise get swept into
# the tail of whichever article happens to precede them.
SECTION_HEADER_RE = re.compile(r"^[IVXLCDM]+\.\d+(?:\.\d+)?\s+[A-ZÁÉÍÓÚÑ][^\n]{0,80}$", re.MULTILINE)

CHAPTER_RE = re.compile(r"CAP[IÍ]TULO\s+([IVXLCDM]+)\s*:\s*([^\n]+)")
ARTICLE_RE = re.compile(r"Art[ií]culo\s+(\d+|Transitorio)\s*:", re.IGNORECASE)

# Each family's marker only starts a new sub-item when it opens an
# enumeration (right after a ':'-terminated sentence) or continues one
# already opened by the previous item of the same family -- otherwise
# it's a cross-reference or line-wrap artifact (e.g. "el Artículo\n60.",
# a date like "\n2018.") rather than a real list marker.
SUBITEM_PATTERNS = [
    ("letter_decimal", re.compile(r"^([a-z])\.(\d+)\)\s+", re.MULTILINE)),
    ("letter", re.compile(r"^([a-z])\)\s+", re.MULTILINE)),
    ("roman", re.compile(r"^([ivx]+)\.\s+", re.MULTILINE)),
    ("number", re.compile(r"^(\d+)\.\s+", re.MULTILINE)),
    ("dash", re.compile(r"^-\s+", re.MULTILINE)),
]
ROMAN_VALUES = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10}


def _real_table_bboxes(page):
    """pdfplumber's default table finder flags the whole page as a single
    giant table on every page of this PDF (it reads the page's border
    rectangle as a table outline); this decree's actual data tables are
    rasterized images with no text layer, so extract_text() already skips
    them. Only bboxes of genuine multi-column, multi-row text tables are
    excluded here, so this is a no-op on the current PDF and only matters
    if a future revision has real vector tables."""
    bboxes = []
    for table in page.find_tables():
        grid = table.extract()
        ncols = max((len(row) for row in grid), default=0)
        if ncols > 1 and len(grid) > 1:
            bboxes.append(table.bbox)
    return bboxes


def _extract_page_text(page):
    bboxes = _real_table_bboxes(page)
    if not bboxes:
        return page.extract_text() or ""

    def outside_tables(obj):
        return not any(
            obj["x0"] >= bx0 and obj["x1"] <= bx1 and obj["top"] >= btop and obj["bottom"] <= bbottom
            for bx0, btop, bx1, bbottom in bboxes
        )

    return page.filter(outside_tables).extract_text() or ""


def extract_document_text(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        pages = [_extract_page_text(page) for page in pdf.pages]
    return FOOTER_RE.sub("", "\n".join(pages))


def isolate_articulado(text):
    """Restricts to Capítulo III onward through the end of the last
    article: Capítulos I-II (general provisions, preliminary definitions)
    precede Fuentes Móviles and aren't coded, and the closing formulas /
    Contraloría annotations after the last article aren't part of the
    articulado either."""
    start_match = START_MARKER_RE.search(text)
    if not start_match:
        sys.exit("Could not locate 'CAPÍTULO III' in the extracted text.")
    end_match = END_MARKER_RE.search(text, start_match.start())
    end = end_match.start() if end_match else len(text)
    return SECTION_HEADER_RE.sub("", text[start_match.start():end])


def split_chapters(text):
    matches = list(CHAPTER_RE.finditer(text))
    chapters = []
    for i, m in enumerate(matches):
        label = f"CAPÍTULO {m.group(1)}: {m.group(2).strip()}"
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chapters.append((label, text[m.end():body_end]))
    return chapters


def split_articles(chapter_body):
    matches = list(ARTICLE_RE.finditer(chapter_body))
    articles = []
    for i, m in enumerate(matches):
        label = f"Artículo {m.group(1)}"
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(chapter_body)
        articles.append((label, chapter_body[m.end():body_end]))
    return articles


def _normalize(chunk):
    return re.sub(r"\s+", " ", chunk).strip()


def _accepted_subitem_matches(article_body):
    accepted = []
    last_value = {}
    for family, pattern in SUBITEM_PATTERNS:
        for m in pattern.finditer(article_body):
            colon_opened = article_body[:m.start()].rstrip().endswith(":")
            prev = last_value.get(family)

            if family == "letter_decimal":
                value = (m.group(1), int(m.group(2)))
                continues = prev is not None and value[0] == prev[0] and value[1] == prev[1] + 1
            elif family == "letter":
                value = m.group(1)
                continues = prev is not None and ord(value) == ord(prev) + 1
            elif family == "roman":
                value = ROMAN_VALUES.get(m.group(1))
                continues = value is not None and prev is not None and value == prev + 1
            elif family == "number":
                value = int(m.group(1))
                continues = prev is not None and value == prev + 1
            else:  # dash bullets have no ordinal value to chain on
                value = True
                continues = prev is not None

            if colon_opened or continues:
                accepted.append((m.start(), m.end()))
                last_value[family] = value
    accepted.sort()
    return accepted


def split_subitems(article_body):
    marks = _accepted_subitem_matches(article_body)
    if not marks:
        text = _normalize(article_body)
        return [(None, text)] if text else []

    chunks = []
    lead = _normalize(article_body[:marks[0][0]])
    if lead:
        chunks.append((None, lead))
    for i, (mstart, mend) in enumerate(marks):
        label = article_body[mstart:mend].strip()
        body_end = marks[i + 1][0] if i + 1 < len(marks) else len(article_body)
        text = _normalize(article_body[mend:body_end])
        if text:
            chunks.append((label, text))
    return chunks


def segment_document(pdf_path):
    """Bakes the article/sub-item markers back into the statement text
    (e.g. "Artículo 4: ...", "a.1) ...") instead of carrying them as
    separate columns, matching the shape of the hand-coded statements in
    original_extracts.json."""
    articulado = isolate_articulado(extract_document_text(pdf_path))
    statements = []
    for _, chapter_body in split_chapters(articulado):
        for article_label, article_body in split_articles(chapter_body):
            for subitem_label, statement_text in split_subitems(article_body):
                prefix = f"{article_label}:" if subitem_label is None else subitem_label
                statements.append(f"{prefix} {statement_text}")
    return [
        {"Statement No.": i, "Raw Statement": text}
        for i, text in enumerate(statements, start=1)
    ]


def main():
    if not PDF_PATH.exists():
        sys.exit(f"PDF not found: {PDF_PATH}")
    rows = segment_document(PDF_PATH)
    OUTPUT_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted {len(rows)} delimited statement chunk(s) from {PDF_PATH.name} -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

#A