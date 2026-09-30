"""Stage 2b: tag Institutional Grammar Object and Object-Property spans as
brat annotations, plus PropertyOf relations linking each property to its
object.

Mirrors tag_attribute.py, but for the four object-related content columns of
PLAN_INSUMO (the DO/IO Reference columns hold statement numbers, not text,
and are intentionally ignored):

  Excel col I  "Direct Object (Content)"     -> DirectObject
  Excel col K  "Direct Object Property"      -> DirectObjectProperty
  Excel col L  "Indirect Object (Content)"   -> IndirectObject
  Excel col N  "Indirect Object Property"    -> IndirectObjectProperty

For every property T-line whose paired object also resolved, a brat relation
line is emitted:

  R{id}\\tPropertyOf Arg1:T{property} Arg2:T{object}

Property-to-object pairing is positional (see PAIRS below): the Excel row
already assigns properties to objects by shared row, and when either cell
holds a ';'/newline-separated list, positional zip preserves that mapping.
Nearest-offset heuristics are deliberately not used -- they can pair the
wrong items when a statement has multiple objects.
"""

import csv
import json
import re

from document_extractor import get_document_text
from matching import (
    BRACKET_RE,
    build_doc_folded,
    find_diacritic_insensitive,
    find_exact,
    find_last_occurrence_before,
    find_last_occurrence_before_folded,
    find_whitespace_insensitive,
    normalize_with_map,
    reject_multiline,
)
from paths import (
    OBJECTS_ANN_PATH,
    STATEMENTS_JSON_PATH,
    UNRESOLVED_OBJECTS_CSV_PATH,
    ensure_outputs_dir,
)
from tag_attribute import find_statement_span

BRACKET_CONTENT_RE = re.compile(r"\[([^\]]*)\]")
FRAGMENT_SPLIT_RE = re.compile(r"[;\n]")
LOGICAL_MARKERS = {"and", "or", "y", "o"}

# Positional pairing: each row in PAIRS defines one (object, property) column
# pair. Fragments in the same index are linked directly by their T-ids at
# write time, matching the Excel schema (properties belong to their column's
# object in the same row).
PAIRS = [
    {
        "object_field": "direct_object",
        "property_field": "direct_object_property",
        "object_label": "DirectObject",
        "property_label": "DirectObjectProperty",
        "object_column": "Direct Object (Content)",
        "property_column": "Direct Object Property",
    },
    {
        "object_field": "indirect_object",
        "property_field": "indirect_object_property",
        "object_label": "IndirectObject",
        "property_label": "IndirectObjectProperty",
        "object_column": "Indirect Object (Content)",
        "property_column": "Indirect Object Property",
    },
]

# T-line emission order (objects first, properties after).
LABEL_ORDER = [p["object_label"] for p in PAIRS] + [p["property_label"] for p in PAIRS]

ALL_COLUMNS = {
    p["object_label"]: p["object_column"] for p in PAIRS
} | {
    p["property_label"]: p["property_column"] for p in PAIRS
}


def split_fragments(value):
    """Split a multi-item Excel cell into non-empty fragments.

    A single-value cell (no ';' or newline) returns a one-element list, so
    callers can treat single- and multi-item cells uniformly.
    """
    if not value:
        return []
    parts = [p.strip() for p in FRAGMENT_SPLIT_RE.split(value)]
    return [p for p in parts if p]


def match_object(statement_text, value):
    """Locate `value` inside `statement_text`.

    Same cascade shape as tag_attribute.match_attribute, plus a final
    diacritic-insensitive tier for values that only differ from the source
    in Spanish accent marks (e.g. Excel "Energetica" vs. doc "Energética").

    Bracket-stripped variants resolve partially bracketed values like
    "[Comercializadores de] leña" to the literal "leña" when only the
    outside part is in the source.

    Returns ((local_start, local_end, matched_text), strategy) or (None, None).
    """
    result = reject_multiline(find_exact(statement_text, value))
    if result:
        return result, "local_exact"

    stripped = BRACKET_RE.sub("", value).strip()
    has_stripped = bool(stripped) and stripped != value

    if has_stripped:
        result = reject_multiline(find_exact(statement_text, stripped))
        if result:
            return result, "local_exact_stripped"

    result = reject_multiline(find_whitespace_insensitive(statement_text, value))
    if result:
        return result, "local_whitespace"

    if has_stripped:
        result = reject_multiline(find_whitespace_insensitive(statement_text, stripped))
        if result:
            return result, "local_whitespace_stripped"

    result = reject_multiline(
        find_whitespace_insensitive(statement_text, value, ignore_case=True)
    )
    if result:
        return result, "local_case_insensitive"

    if has_stripped:
        result = reject_multiline(
            find_whitespace_insensitive(statement_text, stripped, ignore_case=True)
        )
        if result:
            return result, "local_case_insensitive_stripped"

    result = reject_multiline(find_diacritic_insensitive(statement_text, value))
    if result:
        return result, "local_diacritic_insensitive"

    if has_stripped:
        result = reject_multiline(find_diacritic_insensitive(statement_text, stripped))
        if result:
            return result, "local_diacritic_insensitive_stripped"

    return None, None


def match_object_cross_reference(
    doc_text,
    doc_norm,
    doc_norm_map,
    doc_folded,
    folded_to_original,
    value,
    before_index,
):
    """Resolve a value that isn't literally present in its statement span
    by searching backward through the whole document via
    find_last_occurrence_before (nearest earlier hit, never the arbitrary
    first hit in the document). Falls through to a diacritic-insensitive
    backward search if the case-folded backward search finds nothing.

    Only triggered when the Excel cell contains '['. Candidate order:
      - If any non-bracketed text exists (partially bracketed), search for
        that outside portion only. Bracket contents are NOT tried as a
        fallback in this case: the spec says to annotate only the literal
        part outside the brackets.
      - If the value is fully bracketed, search each bracket segment in
        turn, skipping empty and pure logical connectors.

    Returns ((start, end, text), strategy) or (None, None).
    """
    outside = BRACKET_RE.sub("", value).strip()
    if outside:
        candidates = [outside]
    else:
        candidates = []
        for segment in BRACKET_CONTENT_RE.findall(value):
            segment = segment.strip()
            if not segment or segment.lower() in LOGICAL_MARKERS:
                continue
            candidates.append(segment)

    for candidate in candidates:
        result = find_last_occurrence_before(
            doc_text, doc_norm, doc_norm_map, candidate, before_index
        )
        if result:
            return result, "cross_reference"

    for candidate in candidates:
        result = find_last_occurrence_before_folded(
            doc_text, doc_folded, folded_to_original, candidate, before_index
        )
        if result:
            return result, "cross_reference_diacritic_insensitive"

    return None, None


def _resolve(
    doc_text,
    doc_norm,
    doc_norm_map,
    doc_folded,
    folded_to_original,
    stmt_start,
    stmt_end,
    fragment,
):
    """Try to resolve a single fragment to an absolute (start, end, text) span.

    Returns (ann_dict, strategy) on success, else (None, reason_string).
    """
    stmt_text = doc_text[stmt_start:stmt_end]
    local, strategy = match_object(stmt_text, fragment)
    if local is not None:
        ls, le, matched = local
        return {"start": stmt_start + ls, "end": stmt_start + le, "text": matched}, strategy

    if "[" in fragment:
        cross, cross_strategy = match_object_cross_reference(
            doc_text,
            doc_norm,
            doc_norm_map,
            doc_folded,
            folded_to_original,
            fragment,
            stmt_start,
        )
        if cross is not None:
            cs, ce, matched = cross
            return {"start": cs, "end": ce, "text": matched}, cross_strategy

    return None, "no literal match"


def tag_objects(doc_text, statements):
    """Walk statements in order and produce object/property annotations,
    PropertyOf relations, per-strategy counts, and the unresolved log."""
    doc_norm, doc_norm_map = normalize_with_map(doc_text)
    doc_folded, folded_to_original = build_doc_folded(doc_text)

    annotations = {label: [] for label in LABEL_ORDER}
    relations = []  # list of (property_ann, object_ann); linked positionally
    unresolved = []
    strategy_counts = {label: {} for label in LABEL_ORDER}
    total_cells = {label: 0 for label in LABEL_ORDER}

    def log_unresolved(stmt_no, label, fragment, reason):
        unresolved.append(
            {
                "stmt_no": stmt_no,
                "column": ALL_COLUMNS[label],
                "value": fragment,
                "reason": reason,
            }
        )

    cursor = 0
    for stmt in statements:
        span = find_statement_span(
            doc_text, doc_norm, doc_norm_map, stmt["raw_statement"], cursor
        )
        if span is None:
            for pair in PAIRS:
                for label, field in (
                    (pair["object_label"], pair["object_field"]),
                    (pair["property_label"], pair["property_field"]),
                ):
                    for fragment in split_fragments(stmt.get(field)):
                        total_cells[label] += 1
                        log_unresolved(
                            stmt["stmt_no"],
                            label,
                            fragment,
                            "statement span not found in document",
                        )
            continue

        start, end = span
        cursor = end

        for pair in PAIRS:
            obj_frags = split_fragments(stmt.get(pair["object_field"]))
            prop_frags = split_fragments(stmt.get(pair["property_field"]))

            for i in range(max(len(obj_frags), len(prop_frags))):
                obj_frag = obj_frags[i] if i < len(obj_frags) else None
                prop_frag = prop_frags[i] if i < len(prop_frags) else None

                obj_ann = None
                if obj_frag:
                    total_cells[pair["object_label"]] += 1
                    obj_ann, info = _resolve(
                        doc_text,
                        doc_norm,
                        doc_norm_map,
                        doc_folded,
                        folded_to_original,
                        start,
                        end,
                        obj_frag,
                    )
                    if obj_ann is None:
                        log_unresolved(
                            stmt["stmt_no"], pair["object_label"], obj_frag, info
                        )
                    else:
                        obj_ann["stmt_no"] = stmt["stmt_no"]
                        annotations[pair["object_label"]].append(obj_ann)
                        strategy_counts[pair["object_label"]][info] = (
                            strategy_counts[pair["object_label"]].get(info, 0) + 1
                        )

                prop_ann = None
                if prop_frag:
                    total_cells[pair["property_label"]] += 1
                    prop_ann, info = _resolve(
                        doc_text,
                        doc_norm,
                        doc_norm_map,
                        doc_folded,
                        folded_to_original,
                        start,
                        end,
                        prop_frag,
                    )
                    if prop_ann is None:
                        log_unresolved(
                            stmt["stmt_no"], pair["property_label"], prop_frag, info
                        )
                    else:
                        prop_ann["stmt_no"] = stmt["stmt_no"]
                        annotations[pair["property_label"]].append(prop_ann)
                        strategy_counts[pair["property_label"]][info] = (
                            strategy_counts[pair["property_label"]].get(info, 0) + 1
                        )

                if prop_ann is not None:
                    if obj_ann is not None:
                        relations.append((prop_ann, obj_ann))
                    else:
                        reason = (
                            "paired object cell empty in Excel"
                            if obj_frag is None
                            else "paired object did not match"
                        )
                        log_unresolved(
                            stmt["stmt_no"],
                            pair["property_label"],
                            prop_frag,
                            f"tagged but {reason} -- no PropertyOf link",
                        )

    return annotations, relations, strategy_counts, total_cells, unresolved


def _assign_tids(annotations):
    next_id = 1
    for label in LABEL_ORDER:
        for ann in annotations[label]:
            ann["tid"] = f"T{next_id}"
            next_id += 1
    return next_id


def write_annotations(doc_text, annotations, relations, path):
    _assign_tids(annotations)

    with open(path, "w", encoding="utf-8", newline="") as f:
        for label in LABEL_ORDER:
            for ann in annotations[label]:
                slice_ = doc_text[ann["start"]:ann["end"]]
                if slice_ != ann["text"]:
                    raise AssertionError(
                        f"Offset/text mismatch at {ann['tid']} (stmt "
                        f"{ann['stmt_no']}, {label}): "
                        f"doc[{ann['start']}:{ann['end']}]={slice_!r} "
                        f"vs annotated text={ann['text']!r}"
                    )
                f.write(
                    f"{ann['tid']}\t{label} {ann['start']} {ann['end']}\t{ann['text']}\n"
                )

        for rid, (prop_ann, obj_ann) in enumerate(relations, start=1):
            f.write(
                f"R{rid}\tPropertyOf Arg1:{prop_ann['tid']} Arg2:{obj_ann['tid']}\n"
            )


def write_unresolved(unresolved, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["stmt_no", "column", "value", "reason"])
        for row in unresolved:
            writer.writerow([row["stmt_no"], row["column"], row["value"], row["reason"]])


def _sample_t_lines(annotations, label, n=5):
    return [
        f"{ann['tid']}\t{label} {ann['start']} {ann['end']}\t{ann['text']}"
        for ann in annotations[label][:n]
    ]


def _sample_r_lines(relations, n=5):
    return [
        f"R{rid}\tPropertyOf Arg1:{prop_ann['tid']} Arg2:{obj_ann['tid']}"
        for rid, (prop_ann, obj_ann) in enumerate(relations[:n], start=1)
    ]


def main():
    doc_text = get_document_text()

    with open(STATEMENTS_JSON_PATH, "r", encoding="utf-8") as f:
        statements = json.load(f)
    statements.sort(key=lambda s: s["stmt_no"])

    annotations, relations, strategy_counts, total_cells, unresolved = tag_objects(
        doc_text, statements
    )

    ensure_outputs_dir()
    write_annotations(doc_text, annotations, relations, OBJECTS_ANN_PATH)
    write_unresolved(unresolved, UNRESOLVED_OBJECTS_CSV_PATH)

    unresolved_by_col = {}
    for row in unresolved:
        unresolved_by_col[row["column"]] = unresolved_by_col.get(row["column"], 0) + 1

    for label in LABEL_ORDER:
        col_name = ALL_COLUMNS[label]
        matched = len(annotations[label])
        total = total_cells[label]
        print(f"\n== {label} (Excel col: {col_name}) ==")
        print(f"  fragments seen: {total}")
        print(f"  matched: {matched}")
        print(f"  unresolved: {unresolved_by_col.get(col_name, 0)}")
        if strategy_counts[label]:
            print("  matched per strategy:")
            for strategy, n in sorted(
                strategy_counts[label].items(), key=lambda x: -x[1]
            ):
                print(f"    {strategy}: {n}")

    print(f"\nTotal PropertyOf relations: {len(relations)}")

    for label in LABEL_ORDER:
        print(f"\nSample {label} T-lines:")
        for line in _sample_t_lines(annotations, label):
            print(f"  {line}")

    print("\nSample PropertyOf R-lines:")
    for line in _sample_r_lines(relations):
        print(f"  {line}")


if __name__ == "__main__":
    main()
