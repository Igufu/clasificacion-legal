"""For each row of PLAN_INSUMO.xlsx: locate the statement in the official
document, look up its Attribute / Deontic / Direct Object cells **literally**
in that statement's own text, and emit one brat T line per literal span plus
one binary R line per pair of literal spans in the same row.

Relations (binary, one per pair of literal spans in the row):

  R{n}\\tAttrDeontic   Arg1:T{attr}    Arg2:T{deontic}
  R{n}\\tAttrObject    Arg1:T{attr}    Arg2:T{object}
  R{n}\\tDeonticObject Arg1:T{deontic} Arg2:T{object}

No events, no deontic "trigger". A row with just Attribute + Object still
contributes an AttrObject relation; a row with just Attribute still gets a
T line for it. Bracketed Excel values (e.g. `[Titulares de] Buses`,
`[deberá]`) are considered non-literal by definition and dropped. Values
that *are* non-bracketed but can't be found as-is (whitespace aside) in
the statement text are also dropped. Both cases are counted and surfaced
in the summary / HTML as a non-literal ratio.

Inputs:
  - PLAN_INSUMO.xlsx, sheet DECRETO 31 (via nlp-tagging/src/excel_to_json.py)
  - document.txt / leychile_raw.xml (via nlp-tagging/src/document_extractor.py)

Outputs:
  data/triples.ann        T + R lines
  data/triples.txt        copy of document.txt (brat needs same-name .txt)
  data/triples.jsonl      one row per Excel row with any A/D/O cell
  reports/join.csv        per-row: what was found, what was dropped
  reports/edge_cases.csv  bracketed / unmatched / multi-value rows
  reports/literacy.json   per-role literal / non-literal counts for the UI
"""

import csv
import json
import re
from collections import Counter

import openpyxl

from v2_paths import (
    EDGE_CASES_CSV_PATH,
    JOIN_CSV_PATH,
    LITERACY_JSON_PATH,
    TRIPLES_ANN_PATH,
    TRIPLES_JSONL_PATH,
    TRIPLES_TXT_PATH,
    XLSX_PATH,
    ensure_v2_dirs,
    prune_legacy_outputs,
)
from brat_io import load_document_text, t_line, write_doc_copy, write_lines
from build_dataset import compute_statement_spans
from excel_to_json import SHEET_NAME, extract_statements, find_columns
from matching import (
    find_diacritic_insensitive,
    normalize_with_map,
    reject_multiline,
)
from tag_object import split_fragments

# (excel field, brat label, Excel column letter, role key)
ROLES = [
    ("attribute",     "Attribute",    "E", "attribute"),
    ("deontic",       "Deontic",      "G", "deontic"),
    ("direct_object", "DirectObject", "I", "object"),
]
LABEL_OF   = {role: label for _, label, _, role in ROLES}
FIELD_OF   = {role: field for field, _, _, role in ROLES}
COLUMN_OF  = {role: col   for _, _, col, role in ROLES}
ROLE_ORDER = [role for *_, role in ROLES]

RELATION_LABELS = {
    ("attribute", "deontic"): "AttrDeontic",
    ("attribute", "object"):  "AttrObject",
    ("deontic", "object"):    "DeonticObject",
}

LOGICAL_MARKER_RE = re.compile(r"\[\s*(?:AND|OR|Y|O)\s*\]", re.IGNORECASE)


def load_statements():
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True, rich_text=True)
    ws = wb[SHEET_NAME]
    statements = extract_statements(ws, find_columns(ws))
    statements.sort(key=lambda s: s["stmt_no"])
    return statements


def excel_value(stmt, role):
    """Whitespace-collapsed Excel cell for `role` on this row (None if blank)."""
    raw = stmt.get(FIELD_OF[role])
    if raw is None:
        return None
    value, _ = normalize_with_map(raw)
    return value or None


def find_literal(doc_text, stmt_span, value):
    """Return (start, end, matched_text) for the first occurrence of `value`
    inside the statement span. The lookup is whitespace + case + diacritic
    insensitive, so Excel "amoniaco" lands on "amoníaco" in the document;
    bracketed cells are still rejected by the caller before we get here."""
    if stmt_span is None or not value:
        return None
    s, e = stmt_span
    hit = reject_multiline(find_diacritic_insensitive(doc_text[s:e], value))
    if hit is None:
        return None
    local_s, local_e, matched = hit
    return s + local_s, s + local_e, matched


def _match_tier(excel_value, matched_text):
    """verbatim = only whitespace differs from the Excel cell;
    fuzzy    = also required case / Spanish-accent folding."""
    e, _ = normalize_with_map(excel_value)
    m, _ = normalize_with_map(matched_text)
    return "verbatim" if e == m else "fuzzy"


def extract_row(stmt, stmt_span, doc_text):
    """Row-level literal lookup. Returns per-role dict `{role: info}` where
    info is {"value": excel_cell, "literal": bool, "tier": str, "reason":
    str, "span": (start, end), "text": ...}. `tier` is one of:
      - "verbatim"     span text equals the Excel value (whitespace aside)
      - "fuzzy"        matched after case / Spanish-accent folding
      - "non_literal"  bracketed value, empty cell, or no match at all
    Only roles with tier != "non_literal" go to the .ann; everything is
    recorded in the jsonl / join.csv regardless."""
    out = {}
    for role in ROLE_ORDER:
        value = excel_value(stmt, role)
        if value is None:
            out[role] = {"value": None, "literal": False, "tier": "non_literal",
                         "reason": "empty cell"}
            continue
        if stmt_span is None:
            out[role] = {"value": value, "literal": False, "tier": "non_literal",
                         "reason": "statement span not found in document"}
            continue
        if "[" in value:
            out[role] = {"value": value, "literal": False, "tier": "non_literal",
                         "reason": "bracketed (implicit) Excel value"}
            continue
        hit = find_literal(doc_text, stmt_span, value)
        if hit is None:
            out[role] = {"value": value, "literal": False, "tier": "non_literal",
                         "reason": "Excel value not found in statement, even "
                                   "after whitespace / case / accent folding"}
            continue
        start, end, text = hit
        out[role] = {
            "value": value,
            "literal": True,
            "tier": _match_tier(value, text),
            "reason": "",
            "span": (start, end),
            "text": text,
        }
    return out


def collect_entities_and_relations(statements, stmt_spans, doc_text):
    """Second pass: assign consecutive T ids (Attribute, Deontic, DirectObject,
    each in statement order), then build R lines between literal pairs."""
    per_stmt = {}
    for stmt in statements:
        per_stmt[stmt["stmt_no"]] = extract_row(stmt, stmt_spans.get(stmt["stmt_no"]), doc_text)

    # T lines, grouped by label (Attribute first, then Deontic, then DirectObject).
    entities = []
    tid_for = {}  # (stmt_no, role) -> tid
    for role in ROLE_ORDER:
        for stmt in statements:
            info = per_stmt[stmt["stmt_no"]][role]
            if not info["literal"]:
                continue
            tid = len(entities) + 1
            start, end = info["span"]
            entities.append({
                "tid": tid,
                "label": LABEL_OF[role],
                "start": start,
                "end": end,
                "text": info["text"],
                "stmt_no": stmt["stmt_no"],
                "role": role,
            })
            tid_for[(stmt["stmt_no"], role)] = tid

    # R lines: pairs within a row (statement-order).
    relations = []
    for stmt in statements:
        n = stmt["stmt_no"]
        present = [role for role in ROLE_ORDER if (n, role) in tid_for]
        for i, a in enumerate(present):
            for b in present[i + 1:]:
                label = RELATION_LABELS[(a, b)]
                relations.append({
                    "rid": len(relations) + 1,
                    "label": label,
                    "arg1": tid_for[(n, a)],
                    "arg2": tid_for[(n, b)],
                    "stmt_no": n,
                    "roles": (a, b),
                })

    return per_stmt, entities, tid_for, relations


def assemble_outputs(statements, per_stmt, tid_for, relations):
    """Build jsonl rows, join.csv rows, edge-case rows, and the summary
    counters, from the per-row literacy decisions."""
    jsonl_rows, join_rows, edge_rows = [], [], []
    rel_by_stmt = {}
    for r in relations:
        rel_by_stmt.setdefault(r["stmt_no"], []).append(r)

    role_counts = {role: Counter() for role in ROLE_ORDER}

    def flag(kind, stmt_no, role, note, value="", tid=None):
        edge_rows.append({
            "kind": kind,
            "stmt_no": stmt_no,
            "element": role,
            "excel_value": value or "",
            "tid": f"T{tid}" if tid else "",
            "note": note,
        })

    for stmt in statements:
        n = stmt["stmt_no"]
        row = per_stmt[n]
        rels = rel_by_stmt.get(n, [])

        # count literacy per role (verbatim / fuzzy / non-literal / empty)
        for role in ROLE_ORDER:
            info = row[role]
            if info["value"] is None:
                role_counts[role]["empty"] += 1
            elif info["literal"]:
                role_counts[role][info["tier"]] += 1
            else:
                role_counts[role]["non_literal"] += 1

        # edge-case flags
        for role in ROLE_ORDER:
            info = row[role]
            tid = tid_for.get((n, role))
            value = info["value"]
            if value is None:
                flag("empty_cell", n, role, f"Excel column {COLUMN_OF[role]} is empty")
                continue
            if LOGICAL_MARKER_RE.search(value) or len(split_fragments(stmt.get(FIELD_OF[role]))) > 1:
                flag("multi_value", n, role,
                     "';'/newline or [AND]/[OR]; NOT split -- linked as one span" if tid
                     else "';'/newline or [AND]/[OR]; NOT split and no literal span",
                     value, tid)
            if not info["literal"]:
                flag("non_literal", n, role, info["reason"], value)
            elif "[" in value:
                # Only triggers via `info['literal']` branch when a bracketed
                # value is kept, which can't happen here. Left for symmetry.
                flag("bracketed", n, role, info["reason"], value, tid)

        if all(row[role]["value"] is None for role in ROLE_ORDER):
            join_rows.append({"stmt_no": n, "status": "all_cells_empty"})
            continue

        linked = [role for role in ROLE_ORDER if (n, role) in tid_for]
        if len(linked) == 3:
            status = "complete"
        elif len(linked) == 2:
            status = "pair"
        elif len(linked) == 1:
            status = "single"
        else:
            status = "no_literal_span"

        def tid_str(role):
            tid = tid_for.get((n, role))
            return f"T{tid}" if tid else None

        def text_of(role):
            return row[role].get("text")

        def span_of(role):
            return list(row[role]["span"]) if row[role].get("span") else None

        rel_summary = [
            {"label": r["label"], "rid": f"R{r['rid']}",
             "arg1": f"T{r['arg1']}", "arg2": f"T{r['arg2']}",
             "roles": list(r["roles"])}
            for r in rels
        ]

        jsonl_rows.append({
            "statement_no": n,
            "status": status,
            "attribute_text": text_of("attribute"),
            "attribute_span": span_of("attribute"),
            "attribute_tid": tid_str("attribute"),
            "attribute_excel": row["attribute"]["value"],
            "attribute_literal": row["attribute"]["literal"],
            "attribute_tier": row["attribute"]["tier"],
            "attribute_reason": row["attribute"]["reason"],
            "deontic_text": text_of("deontic"),
            "deontic_span": span_of("deontic"),
            "deontic_tid": tid_str("deontic"),
            "deontic_excel": row["deontic"]["value"],
            "deontic_literal": row["deontic"]["literal"],
            "deontic_tier": row["deontic"]["tier"],
            "deontic_reason": row["deontic"]["reason"],
            "object_text": text_of("object"),
            "object_span": span_of("object"),
            "object_tid": tid_str("object"),
            "object_excel": row["object"]["value"],
            "object_literal": row["object"]["literal"],
            "object_tier": row["object"]["tier"],
            "object_reason": row["object"]["reason"],
            "relations": rel_summary,
        })

        join_rows.append({
            "stmt_no": n,
            "status": status,
            "n_literal_roles": len(linked),
            "n_relations": len(rels),
            **{f"{role}_excel":   row[role]["value"] or ""      for role in ROLE_ORDER},
            **{f"{role}_literal": "yes" if row[role]["literal"] else ("empty" if row[role]["value"] is None else "no")
               for role in ROLE_ORDER},
            **{f"{role}_tid":     tid_str(role) or ""           for role in ROLE_ORDER},
            **{f"{role}_text":    (row[role].get("text") or "") for role in ROLE_ORDER},
            **{f"{role}_reason":  row[role]["reason"]           for role in ROLE_ORDER},
        })

    return jsonl_rows, join_rows, edge_rows, role_counts


def write_outputs(doc_text, entities, relations, jsonl_rows, join_rows, edge_rows):
    lines = [t_line(e["tid"], e["label"], e["start"], e["end"], e["text"]) for e in entities]
    lines += [
        f"R{r['rid']}\t{r['label']} Arg1:T{r['arg1']} Arg2:T{r['arg2']}"
        for r in relations
    ]
    write_lines(TRIPLES_ANN_PATH, lines)
    write_doc_copy(doc_text, TRIPLES_TXT_PATH)

    with open(TRIPLES_JSONL_PATH, "w", encoding="utf-8", newline="") as f:
        for row in jsonl_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    join_fields = ["stmt_no", "status", "n_literal_roles", "n_relations"] + [
        f"{role}_{k}" for role in ROLE_ORDER
        for k in ("excel", "literal", "tid", "text", "reason")
    ]
    with open(JOIN_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=join_fields, restval="")
        w.writeheader()
        w.writerows(join_rows)

    edge_fields = ["kind", "stmt_no", "element", "excel_value", "tid", "note"]
    with open(EDGE_CASES_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=edge_fields)
        w.writeheader()
        w.writerows(edge_rows)


def write_literacy(role_counts, relations, status_counter):
    """Snapshot the per-role literacy counts and relation counts used by the
    HTML and the summary. Kept as a tiny json so the viz can read it without
    re-parsing jsonl."""
    rel_counts = Counter(r["label"] for r in relations)
    payload = {
        "roles": {},
        "relations": {label: rel_counts.get(label, 0) for label in RELATION_LABELS.values()},
        "statuses": dict(status_counter),
    }
    for role in ROLE_ORDER:
        c = role_counts[role]
        verbatim = c["verbatim"]
        fuzzy    = c["fuzzy"]
        literal  = verbatim + fuzzy
        non_lit  = c["non_literal"]
        with_val = literal + non_lit
        payload["roles"][role] = {
            "label": LABEL_OF[role],
            "verbatim":    verbatim,
            "fuzzy":       fuzzy,
            "literal":     literal,
            "non_literal": non_lit,
            "empty":       c["empty"],
            "with_value":  with_val,
            "verbatim_ratio":    (verbatim / with_val) if with_val else 0.0,
            "fuzzy_ratio":       (fuzzy    / with_val) if with_val else 0.0,
            "non_literal_ratio": (non_lit  / with_val) if with_val else 0.0,
        }
    with open(LITERACY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


def print_summary(statements, entities, relations, join_rows, edge_rows, literacy):
    status = Counter(r.get("status") for r in join_rows)
    print(f"Excel rows: {len(statements)}")
    print("Row status:")
    for k, v in status.most_common():
        print(f"  {k}: {v}")
    print(f"T lines (literal spans): {len(entities)}")
    rel_by_label = Counter(r["label"] for r in relations)
    print(f"R lines (binary relations): {len(relations)}")
    for label in RELATION_LABELS.values():
        print(f"  {label}: {rel_by_label.get(label, 0)}")
    print("Literacy per role (verbatim / fuzzy / non-literal of with-value):")
    for role in ROLE_ORDER:
        r = literacy["roles"][role]
        if r["with_value"]:
            pct = (f"verbatim={r['verbatim_ratio']:.0%} "
                   f"fuzzy={r['fuzzy_ratio']:.0%} "
                   f"non-lit={r['non_literal_ratio']:.0%}")
        else:
            pct = "n/a"
        print(f"  {r['label']}: {r['verbatim']} + {r['fuzzy']} + {r['non_literal']} "
              f"of {r['with_value']} ({pct})")
    print(f"Edge-case rows flagged: {len(edge_rows)}")
    for k, v in Counter(r["kind"] for r in edge_rows).most_common():
        print(f"  {k}: {v}")


def main():
    prune_legacy_outputs()
    ensure_v2_dirs()

    doc_text = load_document_text()
    statements = load_statements()
    stmt_spans = compute_statement_spans(doc_text, statements)

    per_stmt, entities, tid_for, relations = collect_entities_and_relations(
        statements, stmt_spans, doc_text
    )
    jsonl_rows, join_rows, edge_rows, role_counts = assemble_outputs(
        statements, per_stmt, tid_for, relations
    )

    write_outputs(doc_text, entities, relations, jsonl_rows, join_rows, edge_rows)
    literacy = write_literacy(role_counts, relations,
                              Counter(r.get("status") for r in join_rows))
    print_summary(statements, entities, relations, join_rows, edge_rows, literacy)
    for p in (TRIPLES_ANN_PATH, TRIPLES_JSONL_PATH, JOIN_CSV_PATH,
              EDGE_CASES_CSV_PATH, LITERACY_JSON_PATH):
        print(f"-> {p}")


if __name__ == "__main__":
    main()
