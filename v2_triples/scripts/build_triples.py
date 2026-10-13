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

Outputs:
  data/triples.ann       -- filtered T lines (same ids as filtered.ann) + E lines
  data/triples.txt       -- copy of document.txt
  data/triples.jsonl     -- one line per Excel row with any A/D/O cell
  reports/join.csv       -- one row per Excel row: what was linked, or why not
  reports/edge_cases.csv -- every flagged case (never handled silently)
"""

import csv
import json
import re
from collections import Counter, defaultdict

import openpyxl

from v2_paths import (
    EDGE_CASES_CSV_PATH,
    FILTERED_ANN_PATH,
    FILTERED_ID_MAP_PATH,
    JOIN_CSV_PATH,
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
from matching import normalize_with_map
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


def main():
    doc_text = load_document_text()
    statements = load_statements()
    source = read_ann(SOURCE_ANN_PATH)
    filtered = read_ann(FILTERED_ANN_PATH)
    id_map = read_id_map()

    tid_to_stmt, side = join_source_tids_to_stmt_no(doc_text, statements, source["entities"])
    stmt_spans = compute_statement_spans(doc_text, statements)

    entities = {e["tid"]: e for e in filtered["entities"]}
    by_stmt = defaultdict(dict)  # stmt_no -> {label: new entity}
    for old_tid, new_tid in id_map.items():
        ent = entities[new_tid]
        slot = by_stmt[tid_to_stmt[old_tid]]
        if ent["label"] in slot:
            raise AssertionError(
                f"stmt {tid_to_stmt[old_tid]} has two {ent['label']} spans; needs a decision"
            )
        slot[ent["label"]] = ent

    attr_span_users = defaultdict(list)
    for n, slot in by_stmt.items():
        if "Attribute" in slot:
            a = slot["Attribute"]
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
        slot = by_stmt.get(n, {})
        excel = {}
        for role, field, _, _ in ELEMENTS:
            raw = stmt.get(field)
            excel[role] = normalize_with_map(raw)[0] if raw is not None else None
        linked = {role: slot.get(label) for role, _, label, _ in ELEMENTS}

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
                reasons[role] = missing_reason(role, stmt, side)
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

        present = [r for r in ("attribute", "deontic", "object") if linked[r] is not None]
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
                    for role in ("attribute", "deontic", "object")
                    for k, v in (
                        ("excel", excel[role] or ""),
                        ("tid", tid(role) or ""),
                        ("text", text(role) or ""),
                        ("reason", reasons.get(role, "")),
                    )
                },
            }
        )

    ensure_v2_dirs()
    t_lines = [
        t_line(e["tid"], e["label"], e["start"], e["end"], e["text"]) for e in filtered["entities"]
    ]
    write_lines(TRIPLES_ANN_PATH, t_lines + events)
    write_doc_copy(doc_text, TRIPLES_TXT_PATH)
    with open(TRIPLES_JSONL_PATH, "w", encoding="utf-8", newline="") as f:
        for row in jsonl_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    join_fields = ["stmt_no", "status", "event_id"] + [
        f"{role}_{k}"
        for role in ("attribute", "deontic", "object")
        for k in ("excel", "tid", "text", "reason")
    ]
    with open(JOIN_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=join_fields, restval="")
        writer.writeheader()
        writer.writerows(join_rows)
    edge_fields = ["kind", "stmt_no", "element", "excel_value", "tid", "start", "end", "span_text", "note"]
    with open(EDGE_CASES_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=edge_fields)
        writer.writeheader()
        writer.writerows(edge_rows)

    status_counts = Counter(r["status"] for r in join_rows)
    print(f"Excel rows: {len(statements)}")
    print("Join result by status:")
    for k, v in status_counts.most_common():
        print(f"  {k}: {v}")
    print(f"Events written: {len(events)}")
    print("Edge cases flagged:")
    for k, v in Counter(r["kind"] for r in edge_rows).most_common():
        print(f"  {k}: {v}")
    print("Sample events:")
    for line in events[:5]:
        print(f"  {line}")
    print(f"-> {TRIPLES_ANN_PATH}\n-> {TRIPLES_JSONL_PATH}\n-> {JOIN_CSV_PATH}\n-> {EDGE_CASES_CSV_PATH}")


if __name__ == "__main__":
    main()
