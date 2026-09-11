"""Review stage: split each Attribute annotation into an explicit span and a
normalized label, sharing the same start/end offsets.

- attributes_explicit.ann   -- text = literal source span (brat-valid: matches
  document.txt[start:end] exactly).
- attributes_normalized.ann -- text = the Excel "Attribute" cell value itself
  (the coded, always-animate actor, [bracketed] where the coder marked an
  elided/implicit head). Offsets are identical to the explicit file, so this
  text intentionally will NOT match document.txt[start:end] whenever the
  Excel value differs from the literal span -- that mismatch is the point.
- attribute_diff.csv        -- one row per T#, for reviewing the two side by
  side plus an `is_implicit` flag.

Join key: `stmt_no`. statements.json's `stmt_no` is copied verbatim from the
Excel "Statement No." column by excel_to_json.py, and `tag_attribute.
tag_statements` produces each attribute annotation directly from one
statements.json entry, carrying that entry's stmt_no and raw Excel Attribute
text along with it (see the "stmt_no" / "attribute_excel" keys added to each
annotation dict there). So every T# traces back to exactly one Excel row
through a single, exact, pre-existing shared ID -- there is no ambiguity to
resolve and no fuzzy join is needed.
"""

import csv
import json

from document_extractor import get_document_text
from matching import normalize_with_map
from paths import (
    ATTR_DIFF_CSV_PATH,
    ATTR_EXPLICIT_ANN_PATH,
    ATTR_NORMALIZED_ANN_PATH,
    STATEMENTS_JSON_PATH,
    ensure_outputs_dir,
)
from tag_attribute import tag_statements


def strip_bracket_chars(value):
    """Remove just the '[' / ']' characters, keeping any inner text in place."""
    return value.replace("[", "").replace("]", "")


def normalize_loose(value):
    return " ".join(value.lower().split())


def is_near_exact_substring(excel_stripped, literal_text):
    """True if the bracket-stripped Excel value is literally present in the source.

    Deliberately one-directional: `literal_text` being a substring of
    `excel_stripped` does NOT count (that's exactly the implicit-head
    pattern, e.g. excel "Titulares de vehiculo..." vs. literal "vehiculo...",
    where the excel side is longer because it adds a head the source lacks).
    Only "the excel wording, brackets aside, is found verbatim in the
    source" counts as a near-exact match.
    """
    excel_norm = normalize_loose(excel_stripped)
    literal_norm = normalize_loose(literal_text)
    if not excel_norm or not literal_norm:
        return False
    return excel_norm in literal_norm


def is_implicit_attribute(excel_value, literal_text):
    """True if the Excel value marks an elided head not present in the source.

    A bracket alone isn't enough (a coder may bracket text that also happens
    to appear verbatim); it only counts as implicit when, after dropping the
    bracket characters, the value still isn't a near-exact match of the
    literal span -- i.e. the bracketed content added something the source
    doesn't literally say (e.g. "[Titulares de] Buses").
    """
    if "[" not in excel_value:
        return False
    return not is_near_exact_substring(strip_bracket_chars(excel_value), literal_text)


def main():
    doc_text = get_document_text()

    with open(STATEMENTS_JSON_PATH, "r", encoding="utf-8") as f:
        statements = json.load(f)
    statements.sort(key=lambda s: s["stmt_no"])

    (
        attribute_annotations,
        _deontic_annotations,
        unmatched_attributes,
        _unmatched_deontics,
        unmatched_statements,
    ) = tag_statements(doc_text, statements)

    print(
        "Matching T# -> Excel row via `stmt_no`: statements.json's stmt_no is "
        "copied verbatim from the Excel 'Statement No.' column (excel_to_json.py), "
        "and each attribute annotation is produced directly from one statements.json "
        "entry (tag_attribute.tag_statements), which carries that entry's stmt_no and "
        "raw Excel Attribute text along with it. This is a single, exact, "
        "pre-existing shared ID -- no fuzzy matching or guessing involved."
    )

    ensure_outputs_dir()

    with open(ATTR_EXPLICIT_ANN_PATH, "w", encoding="utf-8", newline="") as f_explicit, open(
        ATTR_NORMALIZED_ANN_PATH, "w", encoding="utf-8", newline=""
    ) as f_normalized, open(ATTR_DIFF_CSV_PATH, "w", encoding="utf-8", newline="") as f_diff:

        writer = csv.writer(f_diff)
        writer.writerow(
            [
                "T_id",
                "start",
                "end",
                "literal_text",
                "excel_attribute",
                "is_implicit",
                "match_source",
            ]
        )

        for i, ann in enumerate(attribute_annotations, start=1):
            tid = f"T{i}"
            start, end = ann["start"], ann["end"]
            literal_text = ann["text"]
            # Excel cells can carry embedded literal newlines (e.g. stmt_no
            # 117); a brat annotation must be a single line, so whitespace
            # (including those newlines) is collapsed same as elsewhere in
            # this pipeline -- brackets are untouched.
            excel_attribute, _ = normalize_with_map(ann["attribute_excel"])

            f_explicit.write(f"{tid}\tAttribute {start} {end}\t{literal_text}\n")
            f_normalized.write(f"{tid}\tAttribute {start} {end}\t{excel_attribute}\n")

            implicit = is_implicit_attribute(excel_attribute, literal_text)
            match_source = ann.get("match_source", "local")
            writer.writerow(
                [tid, start, end, literal_text, excel_attribute, implicit, match_source]
            )

    matched_stmt_nos = {ann["stmt_no"] for ann in attribute_annotations}
    unmatched_stmt_nos = {s["stmt_no"] for s in unmatched_statements}
    unmatched_attr_stmt_nos = {s["stmt_no"] for s in unmatched_attributes}

    no_tid_rows = []
    for stmt in statements:
        if stmt.get("attribute") is None or stmt["stmt_no"] in matched_stmt_nos:
            continue
        if stmt["stmt_no"] in unmatched_stmt_nos:
            reason = "raw_statement span not found in document.txt"
        elif stmt["stmt_no"] in unmatched_attr_stmt_nos:
            reason = "Attribute text not locatable inside its statement span"
        else:
            reason = "unknown"
        no_tid_rows.append((stmt["stmt_no"], stmt["attribute"], reason))

    print(
        f"\nWrote {len(attribute_annotations)} matched T# pairs to "
        f"{ATTR_EXPLICIT_ANN_PATH.name} / {ATTR_NORMALIZED_ANN_PATH.name} / "
        f"{ATTR_DIFF_CSV_PATH.name}"
    )

    print(
        "\nT# with no Excel match: 0 (every T# is minted directly from one "
        "statements.json row with a non-null Attribute value, so this set is "
        "empty by construction)"
    )

    print(f"\nExcel Attribute rows with no T# match ({len(no_tid_rows)}):")
    for stmt_no, attribute, reason in no_tid_rows:
        print(f"  stmt_no={stmt_no}\tattribute={attribute!r}\treason={reason}")


if __name__ == "__main__":
    main()
