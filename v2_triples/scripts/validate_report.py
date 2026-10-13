"""Stage 3: validate filtered.ann / triples.ann / triples.jsonl and write
reports/summary.md.

Checks (any failure is recorded in validation.json and summary.md, and the
script exits non-zero):
  - every T line: document.txt[start:end] == text, no newline, kept label.
    (No normalized Attributes are in v2 -- the source is standoff_comp.ann,
    explicit/literal text only -- so the exact check applies to every entity.)
  - T and E ids consecutive; no unparsed lines; no dangling references.
  - each event: trigger is a Deontic T used by exactly one event; Attribute /
    Object args point at Attribute / DirectObject T lines.
  - triples.ann T lines == filtered.ann T lines.
  - every filtered T maps back (filtered_id_map.csv) to a source T with the
    same label, offsets and text.
  - triples.jsonl agrees with the events (ids, spans, text).
"""

import csv
import json
import sys
from collections import Counter, defaultdict

from v2_paths import (
    EDGE_CASES_CSV_PATH,
    FILTER_LOG_PATH,
    FILTERED_ANN_PATH,
    FILTERED_ID_MAP_PATH,
    JOIN_CSV_PATH,
    SOURCE_ANN_PATH,
    SUMMARY_MD_PATH,
    TRIPLES_ANN_PATH,
    TRIPLES_JSONL_PATH,
    VALIDATION_JSON_PATH,
)
from brat_io import load_document_text, read_ann
from filter_ann import KEEP_LABELS

ROLE_LABELS = {"Attribute": "Attribute", "Object": "DirectObject"}


def validate(doc_text, source, filtered, triples, id_map, jsonl_rows):
    errors = []
    ents = {e["tid"]: e for e in triples["entities"]}

    for name, ann in (("filtered.ann", filtered), ("triples.ann", triples)):
        if ann["other"]:
            errors.append(f"{name}: {len(ann['other'])} unparsed lines")
        if ann["relations"] or ann["attributes"]:
            errors.append(f"{name}: unexpected R/A lines")
        if [e["tid"] for e in ann["entities"]] != list(range(1, len(ann["entities"]) + 1)):
            errors.append(f"{name}: T ids not consecutive")
        for e in ann["entities"]:
            if e["label"] not in KEEP_LABELS:
                errors.append(f"{name}: T{e['tid']} has dropped label {e['label']}")
            if "\n" in e["text"] or "\r" in e["text"]:
                errors.append(f"{name}: T{e['tid']} text contains a newline")
            if doc_text[e["start"]:e["end"]] != e["text"]:
                errors.append(
                    f"{name}: T{e['tid']} doc[{e['start']}:{e['end']}]="
                    f"{doc_text[e['start']:e['end']]!r} != {e['text']!r}"
                )

    if filtered["entities"] != triples["entities"]:
        errors.append("triples.ann T lines differ from filtered.ann")

    src = {e["tid"]: e for e in source["entities"]}
    for old, new in id_map.items():
        s, f = src[old], ents[new]
        if (s["label"], s["start"], s["end"], s["text"]) != (f["label"], f["start"], f["end"], f["text"]):
            errors.append(f"T{new} does not match source T{old}")
    if len(id_map) != len(filtered["entities"]):
        errors.append("id map size != filtered entity count")

    if [e["eid"] for e in triples["events"]] != list(range(1, len(triples["events"]) + 1)):
        errors.append("E ids not consecutive")
    trigger_use = Counter(e["trigger"] for e in triples["events"])
    event_args = {}
    for ev in triples["events"]:
        eid = f"E{ev['eid']}"
        trig = ents.get(ev["trigger"])
        if ev["label"] != "Deontic" or trig is None or trig["label"] != "Deontic":
            errors.append(f"{eid}: trigger is not a Deontic T")
        if trigger_use[ev["trigger"]] > 1:
            errors.append(f"{eid}: trigger T{ev['trigger']} shared by several events")
        roles = Counter(role for role, _ in ev["args"])
        if any(c > 1 for c in roles.values()):
            errors.append(f"{eid}: repeated role")
        args = {}
        for role, ref in ev["args"]:
            target = ents.get(int(ref[1:])) if ref.startswith("T") else None
            if role not in ROLE_LABELS:
                errors.append(f"{eid}: unknown role {role}")
            elif target is None:
                errors.append(f"{eid}: dangling {role}:{ref}")
            elif target["label"] != ROLE_LABELS[role]:
                errors.append(f"{eid}: {role}:{ref} is a {target['label']}")
            args[role] = ref
        args["Deontic"] = f"T{ev['trigger']}"
        event_args[eid] = args

    seen_events = set()
    for row in jsonl_rows:
        eid = row["event_id"]
        if eid is None:
            if row["deontic_tid"] is not None:
                errors.append(f"jsonl stmt {row['statement_no']}: Deontic span but no event")
            continue
        seen_events.add(eid)
        args = event_args.get(eid)
        if args is None:
            errors.append(f"jsonl stmt {row['statement_no']}: {eid} not in triples.ann")
            continue
        for role, key in (("Attribute", "attribute"), ("Deontic", "deontic"), ("Object", "object")):
            if args.get(role) != row[f"{key}_tid"]:
                errors.append(f"jsonl stmt {row['statement_no']}: {role} tid mismatch with {eid}")
                continue
            if row[f"{key}_tid"] is not None:
                e = ents[int(row[f"{key}_tid"][1:])]
                text_key = "deontic_text" if key == "deontic" else f"{key}_text"
                if row[f"{key}_span"] != [e["start"], e["end"]] or row[text_key] != e["text"]:
                    errors.append(f"jsonl stmt {row['statement_no']}: {key} span/text mismatch")
    if seen_events != set(event_args):
        errors.append("events and jsonl rows do not correspond one-to-one")

    return errors


def md_table(rows, cols):
    def cell(v):
        return str(v).replace("|", "\\|").replace("\n", " ")

    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(cell(r.get(c, "")) for c in cols) + " |" for r in rows]
    return out


def details(title, lines):
    return ["<details>", f"<summary>{title}</summary>", ""] + lines + ["", "</details>", ""]


def write_summary(source, filtered, triples, filter_log, join_rows, edge_rows, errors):
    events = triples["events"]
    status = Counter(r["status"] for r in join_rows)
    edge_by_kind = defaultdict(list)
    for r in edge_rows:
        edge_by_kind[r["kind"]].append(r)
    referenced = {e["trigger"] for e in events} | {
        int(ref[1:]) for e in events for _, ref in e["args"]
    }
    unreferenced = Counter(
        e["label"] for e in filtered["entities"] if e["tid"] not in referenced
    )

    L = ["# v2_triples summary", ""]
    L += [
        f"Source: `nlp-tagging/outputs/annotations/{SOURCE_ANN_PATH.name}` (explicit/literal text). "
        "Excel: `PLAN_INSUMO.xlsx`, sheet `DECRETO 31` (E = Attribute, G = Deontic, I = Direct Object).",
        "",
        f"**Validation: {'PASSED' if not errors else f'FAILED ({len(errors)} errors)'}** "
        "(every T: `document.txt[start:end] == text`; consecutive ids; no dangling refs; "
        "events/jsonl consistent). No normalized Attributes are included, so the exact "
        "text check applies to all entities.",
        "",
    ]
    if errors:
        L += ["## Validation errors", ""] + [f"- {e}" for e in errors] + [""]

    L += ["## Entities and relations: before / after filtering", ""]
    labels = list(filter_log["entities_before"])
    rows = [
        {
            "type": lbl,
            "before": filter_log["entities_before"].get(lbl, 0),
            "after": filter_log["entities_after"].get(lbl, 0),
        }
        for lbl in labels
    ]
    rows.append(
        {
            "type": "**T total**",
            "before": len(source["entities"]),
            "after": len(filtered["entities"]),
        }
    )
    for lbl, n in filter_log["relations_before"].items():
        rows.append(
            {"type": f"R {lbl}", "before": n, "after": filter_log["relations_after"].get(lbl, 0)}
        )
    rows.append({"type": "E (events)", "before": 0, "after": len(events)})
    L += md_table(rows, ["type", "before", "after"]) + [""]
    L += [
        f"- All {len(filter_log['dropped_relations'])} PropertyOf relations were dropped "
        "(each touches a DirectObjectProperty / IndirectObjectProperty).",
        f"- {len(filter_log['skipped_non_brat_lines'])} non-brat lines at the end of the source "
        "were skipped: "
        + ", ".join(f"`{x['text']}`" for x in filter_log["skipped_non_brat_lines"] if x["text"]),
        "- Offsets/text unchanged; ids renumbered consecutively (map: `data/filtered_id_map.csv`).",
        "",
    ]

    L += ["## Triples", ""]
    L += md_table(
        [
            {"status": "complete (Attribute + Deontic + Object)", "rows": status["complete"]},
            {"status": "partial event (Deontic + some args)", "rows": status["partial_event"]},
            {"status": "no event (no Deontic span)", "rows": status["no_event"]},
            {"status": "all three cells empty (skipped)", "rows": status["all_cells_empty"]},
            {"status": "**Excel rows total**", "rows": len(join_rows)},
        ],
        ["status", "rows"],
    )
    partial = Counter(r["element"] for r in edge_by_kind["partial_event"])
    L += [
        "",
        f"Events written: **{len(events)}** (one per Deontic span). Partial events lack: "
        + ", ".join(f"{k} = {v}" for k, v in partial.most_common())
        + ".",
        "Filtered entities not referenced by any event: "
        + (", ".join(f"{k} = {v}" for k, v in unreferenced.items()) or "none")
        + ".",
        "",
    ]

    L += ["## Unmatched rows", ""]
    L += [
        "Excel cells with a value but no span (existing matching logic only; no new heuristics). "
        "Full per-row detail: `reports/join.csv`.",
        "",
    ]
    by_reason = defaultdict(list)
    for r in edge_by_kind["unmatched"]:
        by_reason[(r["element"], r["note"])].append(r)
    L += md_table(
        [
            {"element": el, "reason": reason, "count": len(rs)}
            for (el, reason), rs in sorted(by_reason.items(), key=lambda x: -len(x[1]))
        ],
        ["element", "reason", "count"],
    )
    L += [""]
    for (el, reason), rs in sorted(by_reason.items(), key=lambda x: -len(x[1])):
        L += details(
            f"{el}: {reason} ({len(rs)})",
            md_table(rs, ["stmt_no", "excel_value"]),
        )

    L += ["## Flagged edge cases", "", "All rows also in `reports/edge_cases.csv`.", ""]
    sections = [
        (
            "multi_value",
            "Rows with several attributes or objects in one cell",
            "Not split and no cross product: the existing matcher links each cell as a single "
            "span (or none). Needs a decision before any split.",
        ),
        ("empty_cell", "Empty Deontic / Object (or Attribute) cells", "Left empty; no span invented."),
        (
            "bracketed",
            "Bracketed implicit values",
            "Linked to the literal span the offsets point at (the Excel value is kept in "
            "`triples.jsonl` as `*_excel` / `deontic`).",
        ),
        (
            "cross_reference",
            "Spans resolved outside their own statement",
            "Existing backward search found the Attribute in an earlier sentence.",
        ),
        (
            "shared_attribute_span",
            "Attribute spans shared by several statements",
            "Same offsets appear as separate T lines (one per statement), as in the source.",
        ),
    ]
    cols = ["stmt_no", "element", "excel_value", "tid", "start", "end", "span_text", "note"]
    for kind, title, note in sections:
        rs = edge_by_kind[kind]
        L += [f"### {title} ({len(rs)})", "", note, ""]
        if kind == "bracketed":
            notes = Counter((r["element"], r["note"]) for r in rs)
            L += md_table(
                [{"element": e, "note": n_, "count": c} for (e, n_), c in notes.most_common()],
                ["element", "note", "count"],
            ) + [""]
        if not rs:
            continue
        table = md_table(rs, cols)
        L += details("show rows", table) if len(rs) > 30 else table + [""]

    with open(SUMMARY_MD_PATH, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(L) + "\n")


def main():
    doc_text = load_document_text()
    source = read_ann(SOURCE_ANN_PATH)
    filtered = read_ann(FILTERED_ANN_PATH)
    triples = read_ann(TRIPLES_ANN_PATH)
    with open(FILTERED_ID_MAP_PATH, encoding="utf-8", newline="") as f:
        id_map = {int(r["old_tid"][1:]): int(r["new_tid"][1:]) for r in csv.DictReader(f)}
    with open(TRIPLES_JSONL_PATH, encoding="utf-8") as f:
        jsonl_rows = [json.loads(line) for line in f]
    with open(FILTER_LOG_PATH, encoding="utf-8") as f:
        filter_log = json.load(f)
    with open(JOIN_CSV_PATH, encoding="utf-8", newline="") as f:
        join_rows = list(csv.DictReader(f))
    with open(EDGE_CASES_CSV_PATH, encoding="utf-8", newline="") as f:
        edge_rows = list(csv.DictReader(f))

    errors = validate(doc_text, source, filtered, triples, id_map, jsonl_rows)

    with open(VALIDATION_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "passed": not errors,
                "entities_checked": len(triples["entities"]),
                "events_checked": len(triples["events"]),
                "jsonl_rows_checked": len(jsonl_rows),
                "errors": errors,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    write_summary(source, filtered, triples, filter_log, join_rows, edge_rows, errors)

    print(f"Entities checked: {len(triples['entities'])}, events: {len(triples['events'])}, "
          f"jsonl rows: {len(jsonl_rows)}")
    print("Validation PASSED" if not errors else f"Validation FAILED: {len(errors)} errors")
    for e in errors[:20]:
        print(f"  {e}")
    print(f"-> {SUMMARY_MD_PATH}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
