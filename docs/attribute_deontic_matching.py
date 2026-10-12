"""Generate a PDF explaining the Attribute/Deontic matching pipeline.

Run: python3 docs/attribute_deontic_matching.py
Output: docs/attribute_deontic_matching.pdf
"""

from pathlib import Path

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Preformatted,
    Table,
    TableStyle,
    PageBreak,
)


OUT = Path(__file__).parent / "attribute_deontic_matching.pdf"


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            spaceBefore=6,
            spaceAfter=10,
            textColor=colors.HexColor("#1a1a1a"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13.5,
            leading=18,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor("#1a1a1a"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="H3",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=15,
            spaceBefore=8,
            spaceAfter=4,
            textColor=colors.HexColor("#333333"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#555555"),
            spaceAfter=10,
        )
    )
    return styles


def para(text, style):
    return Paragraph(text, style)


def code_block(text):
    return Preformatted(text, ParagraphStyle(
        name="_code",
        fontName="Courier",
        fontSize=8.6,
        leading=11.2,
        leftIndent=8,
        backColor=colors.HexColor("#f4f4f4"),
        borderPadding=6,
        spaceAfter=10,
    ))


def cascade_table(rows):
    header = ["#", "Strategy", "What it does"]
    data = [header] + rows
    tbl = Table(data, colWidths=[0.4 * inch, 2.1 * inch, 4.1 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b3a55")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("LEADING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f9")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tbl


def build():
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=LETTER,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
        title="Attribute & Deontic Matching",
        author="clasificacion-legal / nlp-tagging",
    )

    story = []

    # ---------- Title ----------
    story.append(para("Attribute &amp; Deontic Matching", styles["H1"]))
    story.append(para(
        "How <b>tag_attribute.py</b> and <b>tag_deontic.py</b> convert Excel-coded "
        "Institutional Grammar fields into precise character offsets inside the "
        "official plain-text version of the norma.",
        styles["Body"],
    ))
    story.append(Spacer(1, 4))

    # ---------- 1. Problem ----------
    story.append(para("1. The problem", styles["H2"]))
    story.append(para(
        "Coders annotate each atomistic statement in an Excel spreadsheet "
        "(<b>PLAN_INSUMO.xlsx</b>). For every row they record, among other fields, "
        "an <b>Attribute</b> (the actor / holder) and a <b>Deontic</b> (the modal). "
        "The goal of this stage is to turn each of those Excel fields into a "
        "<b>brat</b>-style annotation — a byte offset range inside the plain text "
        "<b>document.txt</b> — so the annotations can be visualized and reviewed "
        "against the actual legal source.",
        styles["Body"],
    ))
    story.append(para(
        "That mapping is non-trivial because:",
        styles["Body"],
    ))
    story.append(para(
        "&nbsp;&nbsp;&bull;&nbsp; The Excel <i>Raw Statement</i> is a paraphrase of "
        "text that lives in the document, often with different whitespace, "
        "line-wrapping, or minor capitalization.<br/>"
        "&nbsp;&nbsp;&bull;&nbsp; The <i>Attribute</i> is frequently written with "
        "<b>square brackets</b> around implied words (e.g. <font face='Courier'>"
        "\"[Titulares de] fuentes estacionarias\"</font>) — those brackets are "
        "metadata, not literal text in the document.<br/>"
        "&nbsp;&nbsp;&bull;&nbsp; The <i>Deontic</i>'s surface phrase (e.g. "
        "<font face='Courier'>\"deberán\"</font>, or a paraphrase like "
        "<font face='Courier'>\"prohíbe la operación\"</font>) is captured from the "
        "<b>bold run</b> inside the Excel Raw Statement cell and must be located "
        "inside the corresponding stretch of document.txt.",
        styles["Body"],
    ))

    # ---------- 2. Inputs / Outputs ----------
    story.append(para("2. Inputs and outputs", styles["H2"]))
    story.append(para(
        "<b>Inputs</b> (produced by earlier stages):",
        styles["Body"],
    ))
    story.append(code_block(
        "outputs/document.txt      # plain text of the norma\n"
        "outputs/statements.json   # one entry per Excel row, e.g.:\n"
        "  {\n"
        "    \"stmt_no\": 42,\n"
        "    \"raw_statement\": \"Los titulares de fuentes estacionarias deberan ...\",\n"
        "    \"attribute\":     \"[Titulares de] fuentes estacionarias\",\n"
        "    \"deontic\":       \"deberan\",\n"
        "    \"deontic_surface\":\"deberan\"\n"
        "  }"
    ))
    story.append(para("<b>Outputs</b>:", styles["Body"]))
    story.append(code_block(
        "outputs/annotations/document.ann              # brat annotations, surface text\n"
        "outputs/annotations/deontic_literal.ann       # same, but Deontic text = Excel value\n"
        "outputs/unmatched.csv, unmatched_deontic.csv, unmatched_statements.csv"
    ))

    # ---------- 3. Pipeline overview ----------
    story.append(para("3. Pipeline at a glance", styles["H2"]))
    story.append(para(
        "For each statement (in <b>stmt_no</b> order), the tagger does three "
        "things, in this order:",
        styles["Body"],
    ))
    story.append(code_block(
        "for stmt in statements:\n"
        "    (a) span   = find_statement_span(doc, stmt.raw_statement, cursor)\n"
        "    (b) attr   = match_attribute(doc[span], stmt.attribute)\n"
        "                 or match_attribute_cross_reference(doc, stmt.attribute, span.start)\n"
        "    (c) deont  = tag_deontic_for_span(doc, stmt, span.start, span.end)\n"
        "    cursor    = span.end   # move forward; do not re-scan already-tagged prefix"
    ))
    story.append(para(
        "The <b>cursor</b> is important: statements are processed in the same order "
        "they appear in the document, and each next search starts at the previous "
        "statement's end. That prevents an earlier repeated phrase from stealing "
        "the match away from a later, correct occurrence.",
        styles["Body"],
    ))

    story.append(PageBreak())

    # ---------- 4. Primitives ----------
    story.append(para("4. Matching primitives (matching.py)", styles["H2"]))

    story.append(para("4.1 <b>normalize_with_map</b>", styles["H3"]))
    story.append(para(
        "Collapses every run of whitespace (spaces, newlines, tabs) into a single "
        "space and strips ends. Alongside the normalized string it returns an "
        "<b>index map</b> — a list where entry <i>i</i> is the offset in the "
        "<i>original</i> string that normalized character <i>i</i> came from. "
        "That is what allows any match found in the normalized text to be "
        "translated back into precise offsets in the raw <b>document.txt</b>.",
        styles["Body"],
    ))
    story.append(code_block(
        "raw:        \"Los  titulares\\n  de fuentes\"\n"
        "normalized: \"Los titulares de fuentes\"\n"
        "index_map:  [0, 1, 2, 3, 5, 6, ..., 13, 16, 17, 19, ...]  # back to raw offsets"
    ))

    story.append(para("4.2 <b>find_exact</b>", styles["H3"]))
    story.append(para(
        "Plain <font face='Courier'>str.find</font>. Fast path for the common case "
        "where the Excel text is a byte-for-byte substring of the document.",
        styles["Body"],
    ))

    story.append(para("4.3 <b>find_whitespace_insensitive</b>", styles["H3"]))
    story.append(para(
        "Normalizes both haystack and needle with <b>normalize_with_map</b>, "
        "searches in the normalized haystack, then uses the index map to project "
        "the match back to raw offsets. Optional <b>ignore_case</b> handles the "
        "case where Excel's canonical capitalization (\"Buses\") differs from the "
        "document (\"los buses ...\").",
        styles["Body"],
    ))

    story.append(para("4.4 <b>reject_multiline</b>", styles["H3"]))
    story.append(para(
        "A brat annotation is a single line. If a whitespace-insensitive match "
        "spans a raw newline, the annotation cannot be written — so the match is "
        "rejected and the caller falls further down the cascade instead of "
        "producing a broken output.",
        styles["Body"],
    ))

    story.append(para("4.5 <b>find_last_occurrence_before</b>", styles["H3"]))
    story.append(para(
        "Used only for the cross-reference fallback. Given a target string and an "
        "upper-bound offset, it finds the <b>latest</b> occurrence of that string "
        "that ends at or before the bound — walking backward through the document "
        "and skipping any multi-line hit. This lets an Attribute that isn't in the "
        "current statement's own text be resolved to the nearest previous mention.",
        styles["Body"],
    ))

    # ---------- 5. Statement location ----------
    story.append(para("5. Locating the statement span", styles["H2"]))
    story.append(para(
        "Before either the Attribute or the Deontic can be tagged, the "
        "<b>raw_statement</b> text itself must be located inside document.txt. "
        "<b>find_statement_span</b> tries, in order:",
        styles["Body"],
    ))
    story.append(cascade_table([
        ["1", "exact from cursor",         "str.find(raw_statement, cursor) — most common case."],
        ["2", "exact from doc start",      "Retry from offset 0 in case the ordering assumption is wrong."],
        ["3", "whitespace-insensitive",    "Normalize both sides; find first match at or after cursor, then fall back to first match anywhere. Result offsets are mapped back to raw."],
    ]))
    story.append(para(
        "Statements that still cannot be located are dropped into "
        "<b>unmatched_statements.csv</b> — no Attribute or Deontic will be tagged "
        "for them.",
        styles["Body"],
    ))

    story.append(PageBreak())

    # ---------- 6. Attribute matching ----------
    story.append(para("6. Attribute matching", styles["H2"]))

    story.append(para("6.1 Local cascade (inside the statement span)", styles["H3"]))
    story.append(para(
        "<b>match_attribute</b> tries the following strategies against the sliced "
        "<font face='Courier'>doc_text[start:end]</font>, stopping at the first "
        "one that finds a match whose text does not embed a newline:",
        styles["Body"],
    ))
    story.append(cascade_table([
        ["1", "exact",                                  "Literal substring of the statement span."],
        ["2", "exact, brackets stripped",               "Remove any <font face='Courier'>[…]</font> segments from the Excel value first (e.g. \"[Titulares de] fuentes\" &rarr; \"fuentes\")."],
        ["3", "whitespace-insensitive",                 "Same as (1) but tolerant to newline/whitespace differences."],
        ["4", "whitespace-insensitive, stripped",       "Same as (2) but tolerant to whitespace."],
        ["5", "whitespace-insensitive, case-insensitive","Handles \"Buses\" (Excel) vs \"buses\" (document)."],
        ["6", "whitespace-insensitive, stripped, ci",   "Both accommodations at once — last resort."],
    ]))

    story.append(para("6.2 Cross-reference fallback (whole-document lookup)", styles["H3"]))
    story.append(para(
        "When the Attribute contains <b>square brackets</b> and none of the six "
        "local strategies work, coders were signalling that the bracketed material "
        "is implied. Concretely, most rows of the form <font face='Courier'>"
        "\"[Titulares de] X\"</font> or <font face='Courier'>\"Titulares de "
        "[X]\"</font> mean: the actor <b>X</b> (or the role phrase) was already "
        "named explicitly in an earlier sentence of the same article, and this "
        "atomistic statement doesn't restate it.",
        styles["Body"],
    ))
    story.append(para(
        "<b>match_attribute_cross_reference</b> builds a small list of candidate "
        "strings and searches <b>backward</b> from the statement start through the "
        "entire document, taking the nearest previous occurrence:",
        styles["Body"],
    ))
    story.append(code_block(
        "candidates = []\n"
        "outside = brackets_stripped(attribute)               # e.g. \"fuentes estacionarias\"\n"
        "if outside and not generic_role_only(outside):\n"
        "    candidates.append(outside)                       # #1 primary\n"
        "\n"
        "for segment in bracket_contents(attribute):          # e.g. \"Titulares de\"\n"
        "    if segment and segment not in {\"and\", \"or\"} and not generic_role_only(segment):\n"
        "        candidates.append(segment)\n"
        "    object_part = strip_role_prefix(segment)         # \"Titulares de calderas\" -> \"calderas\"\n"
        "    if object_part and object_part != segment and not generic_role_only(object_part):\n"
        "        candidates.append(object_part)\n"
        "\n"
        "for candidate in candidates:\n"
        "    hit = find_last_occurrence_before(doc, doc_norm, doc_norm_map,\n"
        "                                     candidate, before_index=stmt_start)\n"
        "    if hit: return hit"
    ))
    story.append(para(
        "A guard, <b>_is_generic_role_only</b>, discards candidates like "
        "\"Titulares de\" or \"Usuarios\" with no object — those role words recur "
        "throughout legal text and a backward search would confidently land on an "
        "unrelated sentence rather than falling through to \"no match\". "
        "<b>find_last_occurrence_before</b> also rejects any candidate hit that "
        "would span a newline (it retries further back).",
        styles["Body"],
    ))
    story.append(para(
        "When a cross-reference match is used, the annotation is stamped with "
        "<font face='Courier'>match_source = \"cross_reference\"</font>; local "
        "matches are stamped <font face='Courier'>\"local\"</font>. That flag is "
        "what <b>attribute_review.py</b> uses to prioritize human review.",
        styles["Body"],
    ))

    story.append(PageBreak())

    # ---------- 7. Deontic matching ----------
    story.append(para("7. Deontic matching", styles["H2"]))
    story.append(para(
        "The Deontic side is simpler than the Attribute side. The Excel <i>Raw "
        "Statement</i> cell marks the surface phrase that carries the modality "
        "with <b>bold</b> formatting; the earlier extraction stage stores that "
        "bold run under <b>deontic_surface</b>. Sometimes it is the modal itself "
        "(\"deberán\", \"podrán\"), sometimes a future-tense verb that stands in "
        "for an implied <font face='Courier'>[deberá]</font> (\"generará\"), and "
        "sometimes a paraphrase (\"prohíbe la operación\", \"será fiscalizada\").",
        styles["Body"],
    ))
    story.append(para(
        "<b>tag_deontic_for_span</b> is called with the statement's already-"
        "resolved <font face='Courier'>(start, end)</font> — no need to re-locate "
        "the statement. It then runs <b>match_deontic</b>, whose cascade mirrors "
        "<b>match_attribute</b> but without the cross-reference fallback (the "
        "surface phrase, being bold in the Excel Raw Statement, is by construction "
        "present in this statement's own text):",
        styles["Body"],
    ))
    story.append(cascade_table([
        ["1", "exact",                            "Literal substring of the statement span."],
        ["2", "exact, brackets stripped",         "Belt-and-suspenders: a bold run shouldn't contain \"[…]\" but a stray bracket must not defeat the match."],
        ["3", "whitespace-insensitive",           "Tolerant to newline/whitespace differences."],
        ["4", "whitespace-insensitive, stripped", "Both accommodations at once."],
    ]))
    story.append(para(
        "Two rules on when a Deontic is tagged at all:",
        styles["Body"],
    ))
    story.append(para(
        "&nbsp;&nbsp;&bull;&nbsp; If the Excel <b>Deontic</b> cell is blank, the "
        "row is skipped outright — an empty coding is not an unmatched deontic.<br/>"
        "&nbsp;&nbsp;&bull;&nbsp; If <b>deontic_surface</b> is empty, likewise skipped.<br/>"
        "&nbsp;&nbsp;&bull;&nbsp; Otherwise the cascade runs; failure lands in "
        "<b>unmatched_deontic.csv</b>.",
        styles["Body"],
    ))
    story.append(para(
        "Every deontic hit is tagged with the same brat type, plain <b>Deontic</b>. "
        "The Excel <i>Deontic</i> value itself (e.g. \"deberán\", \"[podrán]\") is "
        "kept as the annotation's <b>deontic</b> field, not folded into the type "
        "name — that keeps the brat schema flat and lets the modal token stay "
        "verbatim, including its <font face='Courier'>[…]</font> brackets that "
        "mark implicit modality.",
        styles["Body"],
    ))

    # ---------- 8. Output ----------
    story.append(para("8. Output files", styles["H2"]))
    story.append(para(
        "Two <b>.ann</b> files are written per document (both share the same "
        "spans and only differ in the text stored on each Deontic line):",
        styles["Body"],
    ))
    story.append(code_block(
        "# document.ann  — surface text, i.e. what the document actually says\n"
        "T1  Attribute 152 189   los titulares de fuentes estacionarias\n"
        "T2  Deontic   190 197   deberan\n"
        "\n"
        "# deontic_literal.ann  — Attribute lines identical; Deontic text is the\n"
        "#                       canonical Excel value (may include square brackets)\n"
        "T1  Attribute 152 189   los titulares de fuentes estacionarias\n"
        "T2  Deontic   190 197   [debera]"
    ))
    story.append(para(
        "Both files list all Attribute annotations first (in statement order) and "
        "all Deontic annotations after, each with a unique <font face='Courier'>"
        "T&lt;n&gt;</font> id. That is the exact layout brat expects: one span "
        "per line, tab-separated, <font face='Courier'>&lt;type&gt; &lt;start&gt; "
        "&lt;end&gt; &lt;text&gt;</font>.",
        styles["Body"],
    ))

    # ---------- 9. Failure buckets ----------
    story.append(para("9. Failure buckets", styles["H2"]))
    story.append(para(
        "Anything that cannot be resolved is written to a CSV so a human can "
        "review it — the pipeline never guesses:",
        styles["Body"],
    ))
    story.append(cascade_table([
        ["1", "unmatched_statements.csv", "Raw statement not found in document.txt at all."],
        ["2", "unmatched.csv",            "Statement found but its Attribute couldn't be located locally, and (if bracketed) the cross-reference fallback also failed."],
        ["3", "unmatched_deontic.csv",    "Statement found but its bold deontic_surface couldn't be located in the span."],
    ]))

    doc.build(story)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
