"""Stage 2: join PLAN_INSUMO.xlsx rows to filtered.ann entities and write
Attribute-Deontic-Object triples as brat events.

Join (reuses the existing logic, no new matching):
  The .ann files don't carry stmt_no, so -- like bio_dataset/build_dataset.py
  -- we re-run the existing taggers in memory (tag_attribute.tag_statements,
  tag_object.tag_objects) on the Excel rows. Their output, in write order,
  must reproduce standoff_comp.ann T-for-T (label, start, end, text); this is
  asserted, and if it fails the script stops instead of guessing. Each source
  T id then inherits the stmt_no of the Excel row that produced it (the same
  exact join attribute_review.py documents), and filtered_id_map.csv carries
  it over to the renumbered ids.

Encoding (Deontic spans exist, so triples are events with Deontic as the
trigger):
  E{n}\\tDeontic:T{deontic} Attribute:T{attribute} Object:T{object}
An event is written for every statement with a Deontic span; Attribute /
Object args are included only when that span resolved (partial events are
flagged in the report). Statements without a Deontic span get no event but
still appear in triples.jsonl with null spans.

Two versions are written from the same join:

  inferred -- every span the existing matchers found, including ones they
              "translated" from a non-literal Excel value (bracketed
              "[Titulares de] Buses" -> "buses", "[deberá]" -> "generará",
              cross-references to an earlier sentence, case/accent-folded
              matches).
  literal  -- only spans whose text IS the Excel cell value (whitespace
              aside), inside the statement's own text. See literalize().
              Deontic spans are narrowed from the bold surface phrase to the
              Excel modal itself ("deberán contar" -> "deberán").

Outputs (inferred / literal):
  data/triples.ann        / data/triples_literal.ann    -- T lines + E lines
  data/triples.txt        / data/triples_literal.txt    -- copy of document.txt
  data/triples.jsonl      / data/triples_literal.jsonl  -- one line per Excel row with any A/D/O cell
  reports/join.csv        / reports/join_literal.csv    -- per Excel row: what was linked, or why not
  reports/edge_cases.csv  / reports/edge_cases_literal.csv -- every flagged case
  data/literal_id_map.csv -- literal T id -> the filtered.ann T it came from
"""

import csv
import json
import re
from collections import Counter, defaultdict

import openpyxl

from v2_paths import (
    EDGE_CASES_CSV_PATH,
    FILTERED_ANN_PATH,
    FULL_ANN_PATH,
    FULL_EDGE_CASES_CSV_PATH,
    FULL_ID_MAP_PATH,
    FULL_JOIN_CSV_PATH,
    FULL_JSONL_PATH,
    FULL_TXT_PATH,
    FILTERED_ID_MAP_PATH,
    JOIN_CSV_PATH,
    LITERAL_ANN_PATH,
    LITERAL_EDGE_CASES_CSV_PATH,
    LITERAL_FULL_ANN_PATH,
    LITERAL_FULL_EDGE_CASES_CSV_PATH,
    LITERAL_FULL_ID_MAP_PATH,
    LITERAL_FULL_JOIN_CSV_PATH,
    LITERAL_FULL_JSONL_PATH,
    LITERAL_FULL_TXT_PATH,
    LITERAL_ID_MAP_PATH,
    LITERAL_JOIN_CSV_PATH,
    LITERAL_JSONL_PATH,
    LITERAL_LOG_PATH,
    LITERAL_TXT_PATH,
    SOURCE_ANN_PATH,
    TRIPLES_ANN_PATH,
    TRIPLES_JSONL_PATH,
    TRIPLES_TXT_PATH,
    XLSX_PATH,
    ensure_v2_dirs,
)
from brat_io import load_document_text, read_ann, t_line, write_doc_copy, write_lines
from attribute_review import is_implicit_attribute
from build_dataset import compute_statement_spans
from excel_to_json import SHEET_NAME, extract_statements, find_columns
from matching import (
    find_diacritic_insensitive,
    find_whitespace_insensitive,
    normalize_with_map,
    reject_multiline,
    strip_diacritics_with_map,
)
from tag_attribute import tag_statements
from tag_object import LABEL_ORDER, split_fragments, tag_objects

# (role, statements.json field, brat label, Excel column letter)
ELEMENTS = [
    ("attribute", "attribute", "Attribute", "E"),
    ("deontic", "deontic", "Deontic", "G"),
    ("object", "direct_object", "DirectObject", "I"),
]
EVENT_ROLES = {"attribute": "Attribute", "object": "Object"}
LOGICAL_MARKER_RE = re.compile(r"\[\s*(?:AND|OR|Y|O)\s*\]", re.IGNORECASE)
ROLES = ("attribute", "deontic", "object")
LABEL_OF = {role: label for role, _, label, _ in ELEMENTS}

# Literal version: when False (default) the span must equal the Excel value
# exactly (only whitespace may differ). Set True to also accept spans that
# differ only in case or Spanish accents (e.g. "Buses"/"buses",
# "estandar"/"estándar"); the summary reports how many that would add.
LITERAL_ALLOW_CASE_AND_ACCENTS = False


def load_statements():
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True, rich_text=True)
    ws = wb[SHEET_NAME]
    statements = extract_statements(ws, find_columns(ws))
    statements.sort(key=lambda s: s["stmt_no"])
    return statements


def join_source_tids_to_stmt_no(doc_text, statements, source_entities):
    """Return ({source_tid: stmt_no}, tagger side outputs).

    Rebuilds the exact T sequence merge_literals.py wrote into
    standoff_comp.ann (Attribute, Deontic, then tag_object.LABEL_ORDER) from
    the in-memory annotation dicts, which carry stmt_no.
    """
    attrs, deontics, unmatched_attrs, unmatched_deontics, unmatched_stmts = tag_statements(
        doc_text, statements
    )
    objects, _, _, _, unresolved = tag_objects(doc_text, statements)

    produced = [("Attribute", a) for a in attrs] + [("Deontic", a) for a in deontics]
    for label in LABEL_ORDER:
        produced += [(label, a) for a in objects[label]]

    reproduced = [(lbl, a["start"], a["end"], a["text"]) for lbl, a in produced]
    on_disk = [(e["label"], e["start"], e["end"], e["text"]) for e in source_entities]
    if reproduced != on_disk:
        first_diff = next(
            (i for i, (x, y) in enumerate(zip(reproduced, on_disk)) if x != y),
            min(len(reproduced), len(on_disk)),
        )
        raise AssertionError(
            f"Re-running the taggers does not reproduce {SOURCE_ANN_PATH.name} "
            f"(first difference at T{first_diff + 1}); the stmt_no join would be unreliable."
        )

    tid_to_stmt = {
        ent["tid"]: ann["stmt_no"] for ent, (_, ann) in zip(source_entities, produced)
    }
    side = {
        "unmatched_attrs": {s["stmt_no"] for s in unmatched_attrs},
        "unmatched_deontics": {s["stmt_no"] for s in unmatched_deontics},
        "unmatched_stmts": {s["stmt_no"] for s in unmatched_stmts},
        "object_reasons": {
            r["stmt_no"]: r["reason"]
            for r in unresolved
            if r["column"] == "Direct Object (Content)"
        },
    }
    return tid_to_stmt, side


def read_id_map():
    with open(FILTERED_ID_MAP_PATH, encoding="utf-8", newline="") as f:
        return {int(r["old_tid"][1:]): int(r["new_tid"][1:]) for r in csv.DictReader(f)}


def missing_reason(role, stmt, side):
    n = stmt["stmt_no"]
    if n in side["unmatched_stmts"]:
        return "statement span not found in document"
    if role == "attribute":
        if n in side["unmatched_attrs"]:
            tiers = "local cascade + cross-reference" if "[" in stmt["attribute"] else "local cascade"
            return f"no match ({tiers})"
    elif role == "deontic":
        if not stmt.get("deontic_surface"):
            return "no bold surface phrase in Raw Statement cell"
        if n in side["unmatched_deontics"]:
            return "bold surface phrase not found in statement span"
    elif role == "object":
        if n in side["object_reasons"]:
            return side["object_reasons"][n]
    return "unknown"


def excel_values(stmt):
    """Excel A/D/O cells, whitespace-collapsed like attribute_review.py does."""
    values = {}
    for role, field, _, _ in ELEMENTS:
        raw = stmt.get(field)
        values[role] = normalize_with_map(raw)[0] if raw is not None else None
    return values


def fold_text(value, loose):
    value = normalize_with_map(value)[0]
    return strip_diacritics_with_map(value)[0] if loose else value


def _is_word_bounded(doc_text, start, end):
    before = doc_text[start - 1] if start > 0 else " "
    after = doc_text[end] if end < len(doc_text) else " "
    return not before.isalnum() and not after.isalnum()


def find_literal_word(doc_text, start, end, value, loose):
    """First whole-word occurrence of `value` inside doc_text[start:end].

    Uses the existing matching.py finders: whitespace-insensitive only when
    strict, case + accent-insensitive when `loose`.
    """
    finder = find_diacritic_insensitive if loose else find_whitespace_insensitive
    pos = start
    while pos < end:
        hit = reject_multiline(finder(doc_text[pos:end], value))
        if hit is None:
            return None
        s, e = pos + hit[0], pos + hit[1]
        if _is_word_bounded(doc_text, s, e):
            return s, e
        pos = s + 1
    return None


def literalize(statements, excel_by_stmt, inferred_by_stmt, stmt_spans, doc_text, loose):
    """Keep only the inferred spans that are literally the Excel value.

    A span is literal when the Excel cell has no brackets, the span lies in
    the statement's own text, and its text equals the cell value (only
    whitespace may differ; also case/accents when `loose`). For Deontic the
    span is narrowed to the Excel modal as a whole word inside the bold
    surface phrase. No new search outside the inferred spans is done.

    Returns ({stmt_no: {role: entity}}, {(stmt_no, role): reason dropped}).
    Entities carry `from_tid` (their filtered.ann T) and get `tid` later.
    """
    literal, dropped = defaultdict(dict), {}
    for stmt in statements:
        n = stmt["stmt_no"]
        span = stmt_spans.get(n)
        for role in ROLES:
            value = excel_by_stmt[n][role]
            ent = inferred_by_stmt.get(n, {}).get(role)
            if value is None or ent is None:
                continue
            if "[" in value:
                dropped[(n, role)] = "not literal: bracketed (implicit) Excel value"
                continue
            if not (span and span[0] <= ent["start"] and ent["end"] <= span[1]):
                dropped[(n, role)] = "not literal: span outside the statement's own text"
                continue
            if role == "deontic":
                hit = find_literal_word(doc_text, ent["start"], ent["end"], value, loose)
                if hit is None:
                    dropped[(n, role)] = (
                        "not literal: Excel modal is not a whole word inside the bold surface phrase"
                    )
                    continue
                start, end = hit
            else:
                if fold_text(ent["text"], loose) != fold_text(value, loose):
                    dropped[(n, role)] = "not literal: span text differs from Excel value"
                    continue
                start, end = ent["start"], ent["end"]
            literal[n][role] = {
                "label": ent["label"],
                "start": start,
                "end": end,
                "text": doc_text[start:end],
                "from_tid": ent["tid"],
            }
    return literal, dropped


def number_entities(by_stmt):
    """Assign consecutive T ids in filtered.ann order (Attribute, Deontic,
    DirectObject, each in source order)."""
    order = {LABEL_OF[role]: i for i, role in enumerate(ROLES)}
    ents = [ent for slot in by_stmt.values() for ent in slot.values()]
    ents.sort(key=lambda e: (order[e["label"]], e["from_tid"]))
    for i, ent in enumerate(ents, start=1):
        ent["tid"] = i
    return ents


def assemble(statements, excel_by_stmt, linked_by_stmt, reason_for, stmt_spans):
    """Build events, jsonl rows, join rows and edge-case flags for one version.

    `linked_by_stmt` is {stmt_no: {role: entity}}; `reason_for(role, stmt)`
    explains a non-empty Excel cell that has no linked span.
    """
    attr_span_users = defaultdict(list)
    for n, slot in linked_by_stmt.items():
        if "attribute" in slot:
            a = slot["attribute"]
            attr_span_users[(a["start"], a["end"])].append(n)

    events, jsonl_rows, join_rows, edge_rows = [], [], [], []

    def flag(kind, stmt_no, role, excel_value, ent, note):
        edge_rows.append(
            {
                "kind": kind,
                "stmt_no": stmt_no,
                "element": role,
                "excel_value": excel_value or "",
                "tid": f"T{ent['tid']}" if ent else "",
                "start": ent["start"] if ent else "",
                "end": ent["end"] if ent else "",
                "span_text": ent["text"] if ent else "",
                "note": note,
            }
        )

    for stmt in statements:
        n = stmt["stmt_no"]
        slot = linked_by_stmt.get(n, {})
        excel = excel_by_stmt[n]
        linked = {role: slot.get(role) for role in ROLES}

        if all(v is None for v in excel.values()):
            join_rows.append({"stmt_no": n, "status": "all_cells_empty"})
            continue

        reasons = {}
        for role, field, label, col in ELEMENTS:
            ent = linked[role]
            value = excel[role]
            if value is None:
                if ent is not None:
                    raise AssertionError(f"stmt {n}: {label} span without Excel value")
                flag("empty_cell", n, role, None, None, f"Excel column {col} is empty")
                continue
            if ent is None:
                reasons[role] = reason_for(role, stmt)
                flag("unmatched", n, role, value, None, reasons[role])
            if role != "deontic":
                why = []
                if LOGICAL_MARKER_RE.search(value):
                    why.append("[AND]/[OR] marker")
                if len(split_fragments(stmt[field])) > 1:
                    why.append("';'/newline-separated")
                if why:
                    flag(
                        "multi_value",
                        n,
                        role,
                        value,
                        ent,
                        f"{' + '.join(why)}; NOT split (no cross product) -- "
                        + ("linked as one span by existing matcher" if ent else "no span"),
                    )
            if "[" in value:
                if ent is None:
                    note = "bracketed; no span to link"
                elif is_implicit_attribute(value, ent["text"]):
                    note = "implicit: bracketed text not in source; linked to literal span"
                else:
                    note = "bracketed; literal span contains the bracket-stripped value"
                flag("bracketed", n, role, value, ent, note)
            if ent is not None and role != "deontic" and stmt_spans.get(n):
                st, en = stmt_spans[n]
                if not (ent["start"] >= st and ent["end"] <= en):
                    flag(
                        "cross_reference",
                        n,
                        role,
                        value,
                        ent,
                        f"span lies outside its statement ({st}-{en}); resolved from an earlier mention",
                    )
        a = linked["attribute"]
        if a is not None and len(attr_span_users[(a["start"], a["end"])]) > 1:
            others = [m for m in attr_span_users[(a["start"], a["end"])] if m != n]
            flag(
                "shared_attribute_span",
                n,
                "attribute",
                excel["attribute"],
                a,
                f"same offsets as Attribute of stmt {others}; kept as separate T per statement",
            )

        event_id = None
        if linked["deontic"] is not None:
            event_id = len(events) + 1
            args = [f"Deontic:T{linked['deontic']['tid']}"] + [
                f"{EVENT_ROLES[role]}:T{linked[role]['tid']}"
                for role in ("attribute", "object")
                if linked[role] is not None
            ]
            events.append(f"E{event_id}\t" + " ".join(args))

        present = [r for r in ROLES if linked[r] is not None]
        if len(present) == 3:
            status = "complete"
        elif event_id is not None:
            status = "partial_event"
        else:
            status = "no_event"
        if status == "partial_event":
            missing = [r for r in ("attribute", "object") if linked[r] is None]
            flag("partial_event", n, ",".join(missing), "", None, f"E{event_id} lacks {missing}")

        def span(role):
            ent = linked[role]
            return [ent["start"], ent["end"]] if ent else None

        def text(role):
            ent = linked[role]
            return ent["text"] if ent else None

        def tid(role):
            ent = linked[role]
            return f"T{ent['tid']}" if ent else None

        jsonl_rows.append(
            {
                "statement_no": n,
                "attribute_text": text("attribute"),
                "attribute_span": span("attribute"),
                "deontic": excel["deontic"],
                "object_text": text("object"),
                "object_span": span("object"),
                "event_id": f"E{event_id}" if event_id else None,
                "status": status,
                "attribute_tid": tid("attribute"),
                "attribute_excel": excel["attribute"],
                "deontic_tid": tid("deontic"),
                "deontic_text": text("deontic"),
                "deontic_span": span("deontic"),
                "object_tid": tid("object"),
                "object_excel": excel["object"],
                "missing_reasons": reasons,
            }
        )
        join_rows.append(
            {
                "stmt_no": n,
                "status": status,
                "event_id": f"E{event_id}" if event_id else "",
                **{
                    f"{role}_{k}": v
                    for role in ROLES
                    for k, v in (
                        ("excel", excel[role] or ""),
                        ("tid", tid(role) or ""),
                        ("text", text(role) or ""),
                        ("reason", reasons.get(role, "")),
                    )
                },
            }
        )

    return events, jsonl_rows, join_rows, edge_rows


def write_outputs(doc_text, entities, built, ann_path, txt_path, jsonl_path, join_path, edge_path):
    events, jsonl_rows, join_rows, edge_rows = built
    t_lines = [t_line(e["tid"], e["label"], e["start"], e["end"], e["text"]) for e in entities]
    write_lines(ann_path, t_lines + events)
    write_doc_copy(doc_text, txt_path)
    with open(jsonl_path, "w", encoding="utf-8", newline="") as f:
        for row in jsonl_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    join_fields = ["stmt_no", "status", "event_id"] + [
        f"{role}_{k}" for role in ROLES for k in ("excel", "tid", "text", "reason")
    ]
    with open(join_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=join_fields, restval="")
        writer.writeheader()
        writer.writerows(join_rows)
    edge_fields = ["kind", "stmt_no", "element", "excel_value", "tid", "start", "end", "span_text", "note"]
    with open(edge_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=edge_fields)
        writer.writeheader()
        writer.writerows(edge_rows)


def complete_triples_only(by_stmt):
    """Keep only statements whose Attribute, Deontic and Object all have a
    span. Entities are copied (number_entities renumbers them) and remember
    their filtered.ann T in `from_tid`."""
    return {
        n: {role: {**ent, "from_tid": ent.get("from_tid", ent["tid"])} for role, ent in slot.items()}
        for n, slot in by_stmt.items()
        if all(role in slot for role in ROLES)
    }


def incomplete_reason(by_stmt, kind, fallback):
    """reason_for() for a complete-triples-only version: says which part was
    missing when a statement was dropped for being incomplete, else defers to
    `fallback` (the reason of the version it was filtered from)."""

    def reason(role, stmt):
        slot = by_stmt.get(stmt["stmt_no"], {})
        if role in slot:
            missing = [r for r in ROLES if r not in slot]
            return f"not a full {kind}triple: no {kind}{', '.join(missing)}"
        return fallback(role, stmt)

    return reason


def write_derived_id_map(path, derived_entities, filtered_entities):
    """Derived version's T id -> the filtered.ann T it came from (`narrowed` =
    Deontic cut down to the Excel modal)."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["tid", "filtered_tid", "label", "start", "end", "narrowed"])
        for e in derived_entities:
            src = filtered_entities[e["from_tid"]]
            narrowed = (e["start"], e["end"]) != (src["start"], src["end"])
            writer.writerow([f"T{e['tid']}", f"T{e['from_tid']}", e["label"], e["start"], e["end"], narrowed])


def print_summary(name, statements, built, paths):
    events, _, join_rows, edge_rows = built
    print(f"\n== {name} ==")
    print(f"Excel rows: {len(statements)}")
    print("Join result by status:")
    for k, v in Counter(r["status"] for r in join_rows).most_common():
        print(f"  {k}: {v}")
    print(f"Events written: {len(events)}")
    print("Edge cases flagged:")
    for k, v in Counter(r["kind"] for r in edge_rows).most_common():
        print(f"  {k}: {v}")
    print("Sample events:")
    for line in events[:5]:
        print(f"  {line}")
    for p in paths:
        print(f"-> {p}")


def main():
    doc_text = load_document_text()
    statements = load_statements()
    source = read_ann(SOURCE_ANN_PATH)
    filtered = read_ann(FILTERED_ANN_PATH)
    id_map = read_id_map()

    tid_to_stmt, side = join_source_tids_to_stmt_no(doc_text, statements, source["entities"])
    stmt_spans = compute_statement_spans(doc_text, statements)
    excel_by_stmt = {s["stmt_no"]: excel_values(s) for s in statements}

    role_of = {label: role for role, label in LABEL_OF.items()}
    entities = {e["tid"]: e for e in filtered["entities"]}
    inferred = defaultdict(dict)  # stmt_no -> {role: filtered.ann entity}
    for old_tid, new_tid in id_map.items():
        ent = entities[new_tid]
        slot = inferred[tid_to_stmt[old_tid]]
        role = role_of[ent["label"]]
        if role in slot:
            raise AssertionError(
                f"stmt {tid_to_stmt[old_tid]} has two {ent['label']} spans; needs a decision"
            )
        slot[role] = ent

    ensure_v2_dirs()

    # --- inferred version (all spans the existing matchers found) ---
    built = assemble(
        statements,
        excel_by_stmt,
        inferred,
        lambda role, stmt: missing_reason(role, stmt, side),
        stmt_spans,
    )
    inferred_paths = (TRIPLES_ANN_PATH, TRIPLES_TXT_PATH, TRIPLES_JSONL_PATH, JOIN_CSV_PATH, EDGE_CASES_CSV_PATH)
    write_outputs(doc_text, filtered["entities"], built, *inferred_paths)
    print_summary("inferred (literal + translated)", statements, built, inferred_paths)

    def inferred_reason(role, stmt):
        return missing_reason(role, stmt, side)

    # --- full triples: complete A + D + O in the inferred version ---
    inferred_full = complete_triples_only(inferred)
    inferred_full_entities = number_entities(inferred_full)
    built_inferred_full = assemble(
        statements,
        excel_by_stmt,
        inferred_full,
        incomplete_reason(inferred, "", inferred_reason),
        stmt_spans,
    )
    inferred_full_paths = (
        FULL_ANN_PATH,
        FULL_TXT_PATH,
        FULL_JSONL_PATH,
        FULL_JOIN_CSV_PATH,
        FULL_EDGE_CASES_CSV_PATH,
    )
    write_outputs(doc_text, inferred_full_entities, built_inferred_full, *inferred_full_paths)
    write_derived_id_map(FULL_ID_MAP_PATH, inferred_full_entities, entities)
    print_summary(
        "full triples (inferred + literal)",
        statements,
        built_inferred_full,
        inferred_full_paths + (FULL_ID_MAP_PATH,),
    )

    # --- literal-only version ---
    literal, dropped = literalize(
        statements, excel_by_stmt, inferred, stmt_spans, doc_text, LITERAL_ALLOW_CASE_AND_ACCENTS
    )
    literal_entities = number_entities(literal)

    def literal_reason(role, stmt):
        return dropped.get((stmt["stmt_no"], role)) or (
            f"no inferred span: {inferred_reason(role, stmt)}"
        )

    built_literal = assemble(statements, excel_by_stmt, literal, literal_reason, stmt_spans)
    literal_paths = (
        LITERAL_ANN_PATH,
        LITERAL_TXT_PATH,
        LITERAL_JSONL_PATH,
        LITERAL_JOIN_CSV_PATH,
        LITERAL_EDGE_CASES_CSV_PATH,
    )
    write_outputs(doc_text, literal_entities, built_literal, *literal_paths)
    write_derived_id_map(LITERAL_ID_MAP_PATH, literal_entities, entities)

    # --- full literal triples: literal A + D + O in the same statement ---
    full = complete_triples_only(literal)
    full_entities = number_entities(full)
    built_full = assemble(
        statements,
        excel_by_stmt,
        full,
        incomplete_reason(literal, "literal ", literal_reason),
        stmt_spans,
    )
    full_paths = (
        LITERAL_FULL_ANN_PATH,
        LITERAL_FULL_TXT_PATH,
        LITERAL_FULL_JSONL_PATH,
        LITERAL_FULL_JOIN_CSV_PATH,
        LITERAL_FULL_EDGE_CASES_CSV_PATH,
    )
    write_outputs(doc_text, full_entities, built_full, *full_paths)
    write_derived_id_map(LITERAL_FULL_ID_MAP_PATH, full_entities, entities)

    loose, _ = literalize(statements, excel_by_stmt, inferred, stmt_spans, doc_text, loose=True)
    extra = Counter(
        role for n, slot in loose.items() for role in slot if role not in literal.get(n, {})
    )
    with open(LITERAL_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "allow_case_and_accents": LITERAL_ALLOW_CASE_AND_ACCENTS,
                "case_or_accent_only_differences_excluded": dict(extra),
                "dropped_reasons": dict(Counter(f"{r}: {why}" for (_, r), why in dropped.items())),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print_summary(
        "literal only", statements, built_literal, literal_paths + (LITERAL_ID_MAP_PATH, LITERAL_LOG_PATH)
    )
    if extra:
        print(f"(LITERAL_ALLOW_CASE_AND_ACCENTS=True would add: {dict(extra)})")
    print_summary(
        "full literal triples", statements, built_full, full_paths + (LITERAL_FULL_ID_MAP_PATH,)
    )


if __name__ == "__main__":
    main()
