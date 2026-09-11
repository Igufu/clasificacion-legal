"""Stage 2: tag Institutional Grammar "Attribute" and "Deontic" spans as brat annotations.

Pipeline:
  1. Load the plain text of the norma from outputs/document.txt (produced by
     document_extractor.py; regenerated on demand if missing).
  2. Load outputs/statements.json. For each statement, locate its raw_statement
     text inside document.txt (exact match, else whitespace-insensitive match)
     to get its real start/end offset. Statements that cannot be located are
     logged to outputs/unmatched_statements.csv.
  3. Within each located statement's span:
       a. Locate its attribute text (exact match; else stripping bracketed
          "[implied]" segments; else whitespace-insensitive) and convert to a
          global offset. Attributes that cannot be located are logged to
          outputs/unmatched.csv.
       b. Locate its deontic surface phrase (the bold run captured from the
          Excel Raw Statement cell — see tag_deontic.py). Unmatched deontics
          are logged to outputs/unmatched_deontic.csv.
  4. Write outputs/document.ann with one line per matched span, Attribute
     annotations first (in statement order) then Deontic annotations.
"""

import bisect
import csv
import json
import re

from document_extractor import get_document_text
from matching import (
    BRACKET_RE,
    find_exact,
    find_last_occurrence_before,
    find_whitespace_insensitive,
    normalize_with_map,
    reject_multiline,
)
from paths import (
    DOC_ANN_PATH,
    DOC_DEONTIC_LABEL_ANN_PATH,
    STATEMENTS_JSON_PATH,
    UNMATCHED_CSV_PATH,
    UNMATCHED_DEONTIC_CSV_PATH,
    UNMATCHED_STATEMENTS_CSV_PATH,
    ensure_outputs_dir,
)
from tag_deontic import tag_deontic_for_span


def find_statement_span(doc, doc_norm, doc_norm_map, raw_statement, search_from):
    idx = doc.find(raw_statement, search_from)
    if idx == -1:
        idx = doc.find(raw_statement)
    if idx != -1:
        return idx, idx + len(raw_statement)

    raw_norm, _ = normalize_with_map(raw_statement)
    if not raw_norm:
        return None

    norm_from = bisect.bisect_left(doc_norm_map, search_from)
    idx = doc_norm.find(raw_norm, norm_from)
    if idx == -1:
        idx = doc_norm.find(raw_norm)
    if idx == -1:
        return None

    start = doc_norm_map[idx]
    end = doc_norm_map[idx + len(raw_norm) - 1] + 1
    return start, end


def match_attribute(statement_text, attribute):
    """Try to locate `attribute` inside `statement_text`.

    Returns (local_start, local_end, matched_text) or None.
    """
    result = reject_multiline(find_exact(statement_text, attribute))
    if result:
        return result

    stripped = BRACKET_RE.sub("", attribute).strip()

    if stripped:
        result = reject_multiline(find_exact(statement_text, stripped))
        if result:
            return result

    result = reject_multiline(find_whitespace_insensitive(statement_text, attribute))
    if result:
        return result

    if stripped:
        result = reject_multiline(find_whitespace_insensitive(statement_text, stripped))
        if result:
            return result

    # Case-insensitive fallback: Excel normalizes actor names to a canonical
    # capitalization (e.g. "Buses") that may appear lower-cased in the source
    # ("los buses...").
    result = reject_multiline(
        find_whitespace_insensitive(statement_text, attribute, ignore_case=True)
    )
    if result:
        return result

    if stripped:
        result = reject_multiline(
            find_whitespace_insensitive(statement_text, stripped, ignore_case=True)
        )
        if result:
            return result

    return None


BRACKET_CONTENT_RE = re.compile(r"\[([^\]]*)\]")
_ROLE_WORD = r"(?:titular(?:es)?|usuario(?:s)?)"
ROLE_PREFIX_RE = re.compile(rf"^\s*{_ROLE_WORD}\s+(?:de|del)\s+", re.IGNORECASE)
GENERIC_ROLE_ONLY_RE = re.compile(rf"^\s*{_ROLE_WORD}\s*(?:de|del)?\s*$", re.IGNORECASE)
LOGICAL_MARKERS = {"and", "or"}


def _is_generic_role_only(text):
    """True for bare role words like "Titulares de" or "Usuarios" with no
    object attached -- too generic to search for on their own (the phrase
    recurs throughout the document, so a backward search would confidently
    land on an unrelated, wrong sentence instead of correctly falling
    through to "no match")."""
    return bool(GENERIC_ROLE_ONLY_RE.fullmatch(text.strip()))


def match_attribute_cross_reference(doc_text, doc_norm, doc_norm_map, attribute, before_index):
    """Resolve an Attribute that isn't literally present in this statement's
    own text by searching backward through the whole document for it.

    This dataset's Attribute values are almost always "Titulares de X" /
    "Usuarios de X" (the legal "holder/user of X" role), most often written
    as "[Titulares de] X" -- bracketing just the role phrase because the
    object X was already introduced earlier in the same Article, and this
    (later, atomistic) statement never restates it. So the primary candidate
    is the bracket-stripped remainder itself (the object, e.g. "fuentes
    estacionarias"). Some rows instead bracket the object directly (e.g.
    "Titulares de [calderas]", or a fully-elided "[Ministerio de
    Transportes y Telecomunicaciones]"), so each bracketed segment is also
    tried, together with that segment stripped of a leading "Titulares
    de"/"Usuarios de" role prefix -- i.e. mapping the object back to its
    titular.

    Returns (start, end, matched_text) in absolute document offsets, or None.
    """
    candidates = []

    outside = BRACKET_RE.sub("", attribute).strip()
    if outside and not _is_generic_role_only(outside):
        candidates.append(outside)

    for segment in BRACKET_CONTENT_RE.findall(attribute):
        segment = segment.strip()
        if not segment or segment.lower() in LOGICAL_MARKERS:
            continue
        if not _is_generic_role_only(segment):
            candidates.append(segment)
        object_part = ROLE_PREFIX_RE.sub("", segment).strip()
        if object_part and object_part != segment and not _is_generic_role_only(object_part):
            candidates.append(object_part)

    for candidate in candidates:
        result = find_last_occurrence_before(
            doc_text, doc_norm, doc_norm_map, candidate, before_index
        )
        if result:
            return result

    return None


def tag_statements(doc_text, statements):
    """Walk statements in order and produce annotations + unmatched buckets."""
    doc_norm, doc_norm_map = normalize_with_map(doc_text)

    attribute_annotations = []
    deontic_annotations = []
    unmatched_attributes = []
    unmatched_deontics = []
    unmatched_statements = []

    cursor = 0
    for stmt in statements:
        span = find_statement_span(
            doc_text, doc_norm, doc_norm_map, stmt["raw_statement"], cursor
        )
        if span is None:
            unmatched_statements.append(stmt)
            continue

        start, end = span
        cursor = end

        attribute = stmt.get("attribute")
        if attribute is not None:
            match = match_attribute(doc_text[start:end], attribute)
            if match is not None:
                local_start, local_end, matched_text = match
                attribute_annotations.append(
                    {
                        "stmt_no": stmt["stmt_no"],
                        "start": start + local_start,
                        "end": start + local_end,
                        "text": matched_text,
                        "attribute_excel": attribute,
                        "match_source": "local",
                    }
                )
            elif "[" in attribute:
                cross_match = match_attribute_cross_reference(
                    doc_text, doc_norm, doc_norm_map, attribute, start
                )
                if cross_match is None:
                    unmatched_attributes.append(stmt)
                else:
                    cross_start, cross_end, matched_text = cross_match
                    attribute_annotations.append(
                        {
                            "stmt_no": stmt["stmt_no"],
                            "start": cross_start,
                            "end": cross_end,
                            "text": matched_text,
                            "attribute_excel": attribute,
                            "match_source": "cross_reference",
                        }
                    )
            else:
                unmatched_attributes.append(stmt)

        # A blank Excel "Deontic" cell means the coder made no deontic call for
        # this row; skip it outright rather than falling back to the bold
        # surface phrase as a substitute label (an empty field is left empty,
        # not logged as an unmatched/failed deontic).
        if stmt.get("deontic") is not None and stmt.get("deontic_surface"):
            deontic_ann = tag_deontic_for_span(doc_text, stmt, start, end)
            if deontic_ann is None:
                unmatched_deontics.append(stmt)
            else:
                deontic_annotations.append(deontic_ann)

    return (
        attribute_annotations,
        deontic_annotations,
        unmatched_attributes,
        unmatched_deontics,
        unmatched_statements,
    )


def write_annotations(attribute_annotations, deontic_annotations, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        tid = 1
        for ann in attribute_annotations:
            f.write(f"T{tid}\tAttribute {ann['start']} {ann['end']}\t{ann['text']}\n")
            tid += 1
        for ann in deontic_annotations:
            ann_type = ann.get("type") or "Deontic"
            f.write(f"T{tid}\t{ann_type} {ann['start']} {ann['end']}\t{ann['text']}\n")
            tid += 1


def write_deontic_label_annotations(attribute_annotations, deontic_annotations, path):
    """Like `write_annotations`, but each Deontic line's text is the Excel
    "Deontic" cell value itself (e.g. "deberán", "[deberá]", "no [podrán]")
    rather than the matched surface phrase — still tagged plain "Deontic".

    Brackets are kept exactly as written in the Excel column to mark
    implicit modality; only surrounding/internal whitespace is normalized.
    """
    with open(path, "w", encoding="utf-8", newline="") as f:
        tid = 1
        for ann in attribute_annotations:
            f.write(f"T{tid}\tAttribute {ann['start']} {ann['end']}\t{ann['text']}\n")
            tid += 1
        for ann in deontic_annotations:
            label, _ = normalize_with_map(ann["deontic"])
            f.write(f"T{tid}\tDeontic {ann['start']} {ann['end']}\t{label}\n")
            tid += 1


def write_unmatched(rows, path, extra_field=None):
    """Write unmatched rows to CSV. `extra_field` names the value column (else 'attribute')."""
    value_field = extra_field or "attribute"
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["stmt_no", value_field, "raw_statement"])
        for stmt in rows:
            writer.writerow([stmt["stmt_no"], stmt.get(value_field), stmt["raw_statement"]])


def main():
    doc_text = get_document_text()

    with open(STATEMENTS_JSON_PATH, "r", encoding="utf-8") as f:
        statements = json.load(f)
    statements.sort(key=lambda s: s["stmt_no"])

    (
        attribute_annotations,
        deontic_annotations,
        unmatched_attributes,
        unmatched_deontics,
        unmatched_statements,
    ) = tag_statements(doc_text, statements)

    ensure_outputs_dir()
    write_annotations(attribute_annotations, deontic_annotations, DOC_ANN_PATH)
    write_deontic_label_annotations(
        attribute_annotations, deontic_annotations, DOC_DEONTIC_LABEL_ANN_PATH
    )
    write_unmatched(unmatched_attributes, UNMATCHED_CSV_PATH)
    write_unmatched(unmatched_statements, UNMATCHED_STATEMENTS_CSV_PATH)
    write_unmatched(
        unmatched_deontics, UNMATCHED_DEONTIC_CSV_PATH, extra_field="deontic_surface"
    )

    total = len(statements)
    with_attribute = sum(1 for s in statements if s.get("attribute") is not None)
    with_deontic_surface = sum(1 for s in statements if s.get("deontic_surface"))
    located = total - len(unmatched_statements)

    print(f"Total statements: {total}")
    print(
        f"Statements located in official document: {located} "
        f"(unmatched: {len(unmatched_statements)})"
    )
    print(f"Statements with an attribute: {with_attribute}")
    print(f"Tagged attributes: {len(attribute_annotations)}")
    print(f"Unmatched attributes: {len(unmatched_attributes)}")
    print(f"Statements with a deontic surface phrase (bold): {with_deontic_surface}")
    print(f"Tagged deontics: {len(deontic_annotations)}")
    print(f"Unmatched deontics: {len(unmatched_deontics)}")


if __name__ == "__main__":
    main()
