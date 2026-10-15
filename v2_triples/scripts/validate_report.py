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
  - literal version (triples_literal.ann / .jsonl): the same structural
    checks, plus each literal T comes from a filtered.ann T of the same label
    (identical span, or a sub-span for a narrowed Deontic) and its text equals
    the non-bracketed Excel value.
  - full literal triples (triples_literal_full.ann / .jsonl): the literal
    checks, plus every event is complete and every T belongs to an event.
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
    FULL_ANN_PATH,
    FULL_ID_MAP_PATH,
    FULL_JSONL_PATH,
    LITERAL_ANN_PATH,
    LITERAL_FULL_ANN_PATH,
    LITERAL_FULL_ID_MAP_PATH,
    LITERAL_FULL_JSONL_PATH,
    LITERAL_ID_MAP_PATH,
    LITERAL_JOIN_CSV_PATH,
    LITERAL_JSONL_PATH,
    LITERAL_LOG_PATH,
    SOURCE_ANN_PATH,
    SUMMARY_MD_PATH,
    TRIPLES_ANN_PATH,
    TRIPLES_JSONL_PATH,
    VALIDATION_JSON_PATH,
)
from brat_io import load_document_text, read_ann
from build_triples import LITERAL_ALLOW_CASE_AND_ACCENTS, fold_text
from filter_ann import KEEP_LABELS

ROLE_LABELS = {"Attribute": "Attribute", "Object": "DirectObject"}


def check_ann(name, ann, doc_text):
    """Per-file checks shared by every .ann the pipeline writes."""
    errors = []
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
    return errors


def check_events_and_jsonl(name, triples, jsonl_rows):
    """Event structure + agreement between a triples .ann and its jsonl."""
    errors = []
    ents = {e["tid"]: e for e in triples["entities"]}
    if [e["eid"] for e in triples["events"]] != list(range(1, len(triples["events"]) + 1)):
        errors.append(f"{name}: E ids not consecutive")
    trigger_use = Counter(e["trigger"] for e in triples["events"])
    event_args = {}
    for ev in triples["events"]:
        eid = f"{name} E{ev['eid']}"
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
        event_args[f"E{ev['eid']}"] = args

    seen_events = set()
    for row in jsonl_rows:
        where = f"{name} jsonl stmt {row['statement_no']}"
        eid = row["event_id"]
        if eid is None:
            if row["deontic_tid"] is not None:
                errors.append(f"{where}: Deontic span but no event")
            continue
        seen_events.add(eid)
        args = event_args.get(eid)
        if args is None:
            errors.append(f"{where}: {eid} not in {name}")
            continue
        for role, key in (("Attribute", "attribute"), ("Deontic", "deontic"), ("Object", "object")):
            if args.get(role) != row[f"{key}_tid"]:
                errors.append(f"{where}: {role} tid mismatch with {eid}")
                continue
            if row[f"{key}_tid"] is not None:
                e = ents[int(row[f"{key}_tid"][1:])]
                text_key = "deontic_text" if key == "deontic" else f"{key}_text"
                if row[f"{key}_span"] != [e["start"], e["end"]] or row[text_key] != e["text"]:
                    errors.append(f"{where}: {key} span/text mismatch")
    if seen_events != set(event_args):
        errors.append(f"{name}: events and jsonl rows do not correspond one-to-one")
    return errors


def validate(doc_text, source, filtered, triples, id_map, jsonl_rows):
    """Inferred version: filtered.ann + triples.ann + triples.jsonl."""
    errors = check_ann("filtered.ann", filtered, doc_text)
    errors += check_ann("triples.ann", triples, doc_text)

    if filtered["entities"] != triples["entities"]:
        errors.append("triples.ann T lines differ from filtered.ann")

    ents = {e["tid"]: e for e in triples["entities"]}
    src = {e["tid"]: e for e in source["entities"]}
    for old, new in id_map.items():
        s, f = src[old], ents[new]
        if (s["label"], s["start"], s["end"], s["text"]) != (f["label"], f["start"], f["end"], f["text"]):
            errors.append(f"T{new} does not match source T{old}")
    if len(id_map) != len(filtered["entities"]):
        errors.append("id map size != filtered entity count")

    return errors + check_events_and_jsonl("triples.ann", triples, jsonl_rows)


def validate_full_triples(name, ann, jsonl_rows):
    """Full-literal-triples version: every event has Attribute + Object, and
    every T is used by an event (nothing outside a complete triple)."""
    errors = []
    for ev in ann["events"]:
        if sorted(role for role, _ in ev["args"]) != ["Attribute", "Object"]:
            errors.append(f"{name}: E{ev['eid']} is not a complete triple")
    used = {ev["trigger"] for ev in ann["events"]} | {
        int(ref[1:]) for ev in ann["events"] for _, ref in ev["args"]
    }
    for e in ann["entities"]:
        if e["tid"] not in used:
            errors.append(f"{name}: T{e['tid']} is not part of any triple")
    for row in jsonl_rows:
        if row["event_id"] is not None and row["status"] != "complete":
            errors.append(f"{name} jsonl stmt {row['statement_no']}: event is not complete")
    return errors


def validate_derived(name, doc_text, filtered, ann, tid_map, jsonl_rows, exact_spans=False):
    """A version derived from filtered.ann (literal / full triples): same
    structural checks, plus every T comes from a filtered.ann T of the same
    label with the same span -- or, unless `exact_spans`, a sub-span for a
    narrowed Deontic."""
    errors = check_ann(name, ann, doc_text)
    errors += check_events_and_jsonl(name, ann, jsonl_rows)

    filt = {e["tid"]: e for e in filtered["entities"]}
    if sorted(tid_map) != [e["tid"] for e in ann["entities"]]:
        errors.append(f"{name}: id map does not cover exactly its T lines")
    for e in ann["entities"]:
        src = filt.get(tid_map.get(e["tid"]))
        if src is None or src["label"] != e["label"]:
            errors.append(f"{name}: T{e['tid']} has no filtered.ann T of the same label")
        elif not (src["start"] <= e["start"] and e["end"] <= src["end"]):
            errors.append(f"{name}: T{e['tid']} is not inside filtered T{src['tid']}")
        elif (exact_spans or e["label"] != "Deontic") and (src["start"], src["end"]) != (e["start"], e["end"]):
            errors.append(f"{name}: T{e['tid']} changed offsets of filtered T{src['tid']}")
    return errors


def validate_literal(doc_text, filtered, literal, literal_map, jsonl_rows, name="triples_literal.ann"):
    """Literal version: the derived-version checks, plus every linked span's
    text must BE the (non-bracketed) Excel value."""
    errors = validate_derived(name, doc_text, filtered, literal, literal_map, jsonl_rows)

    for row in jsonl_rows:
        for key, text_key, excel_key in (
            ("attribute", "attribute_text", "attribute_excel"),
            ("deontic", "deontic_text", "deontic"),
            ("object", "object_text", "object_excel"),
        ):
            text, excel = row[text_key], row[excel_key]
            if text is None:
                continue
            if excel is None or "[" in excel:
                errors.append(f"{name} jsonl stmt {row['statement_no']}: {key} linked to a bracketed/empty cell")
            elif fold_text(text, LITERAL_ALLOW_CASE_AND_ACCENTS) != fold_text(excel, LITERAL_ALLOW_CASE_AND_ACCENTS):
                errors.append(
                    f"{name} jsonl stmt {row['statement_no']}: {key} text {text!r} != Excel {excel!r}"
                )
    return errors


def md_table(rows, cols):
    def cell(v):
        return str(v).replace("|", "\\|").replace("\n", " ")

    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(cell(r.get(c, "")) for c in cols) + " |" for r in rows]
    return out


def details(title, lines):
    return ["<details>", f"<summary>{title}</summary>", ""] + lines + ["", "</details>", ""]


def literal_section(filtered, triples, join_rows, literal):
    """Summary lines comparing the inferred and literal-only versions."""
    lit_ann, lit_join, lit_log = literal["ann"], literal["join_rows"], literal["log"]
    full_ann, full_jsonl = literal["full_ann"], literal["full_jsonl"]

    # (column, ann, per-statement statuses) for every version
    versions = [
        ("inferred", triples, [r["status"] for r in join_rows]),
        ("full triples", literal["inferred_full_ann"],
         [r["status"] for r in literal["inferred_full_jsonl"]]),
        ("literal", lit_ann, [r["status"] for r in lit_join]),
        ("full literal triples", full_ann, [r["status"] for r in full_jsonl]),
    ]
    cols = [name for name, _, _ in versions]

    def row(label, value_of):
        return {"": label, **{name: value_of(ann, st) for name, ann, st in versions}}

    L = ["## Versions compared", ""]
    L += [
        "- **inferred** (`triples.*`): every span the matchers found, incl. ones inferred from "
        "non-literal Excel values.",
        "- **full triples** (`triples_full.*`): inferred, restricted to statements with an "
        "Attribute, Deontic **and** Object span.",
        "- **literal** (`triples_literal.*`): only spans whose text is the Excel value (below).",
        "- **full literal triples** (`triples_literal_full.*`): literal, restricted to complete "
        "triples.",
        "",
    ]
    rows = [
        row(lbl, lambda ann, st, lbl=lbl: sum(1 for e in ann["entities"] if e["label"] == lbl))
        for lbl in KEEP_LABELS
    ]
    rows += [
        row("**T total**", lambda ann, st: len(ann["entities"])),
        row("E (events)", lambda ann, st: len(ann["events"])),
    ]
    rows += [
        row(f"rows: {k}", lambda ann, st, k=k: st.count(k))
        for k in ("complete", "partial_event", "no_event")
    ]
    L += md_table(rows, [""] + cols) + [""]

    L += ["## Literal-only version", ""]
    L += [
        "`data/triples_literal.ann` / `.jsonl` keep only spans whose text **is** the Excel cell "
        "value, found inside the statement's own text: no bracketed (implicit) values, no "
        "cross-references to earlier sentences, no case/accent-folded matches"
        + (" (case/accent differences ARE allowed: `LITERAL_ALLOW_CASE_AND_ACCENTS = True`)"
           if lit_log["allow_case_and_accents"] else "")
        + ". Deontic spans are narrowed from the bold surface phrase to the Excel modal itself "
        "(e.g. `deberán contar` → `deberán`). Same partial-event rule as the inferred version.",
        "",
    ]

    L += [
        "### Full literal triples",
        "",
        "`data/triples_literal_full.ann` / `.jsonl`: the literal version restricted to statements "
        "whose Attribute, Deontic **and** Object are all literal. Every event is a complete "
        "triple and every span belongs to one.",
        "",
    ]
    L += md_table(
        [
            {"stmt_no": r["statement_no"], "event": r["event_id"], "attribute": r["attribute_text"],
             "deontic": r["deontic_text"], "object": r["object_text"]}
            for r in full_jsonl if r["status"] == "complete"
        ],
        ["stmt_no", "event", "attribute", "deontic", "object"],
    ) + [""]

    L += ["Why inferred spans were dropped:", ""]
    L += md_table(
        [{"element_reason": k, "count": v} for k, v in sorted(lit_log["dropped_reasons"].items(), key=lambda x: -x[1])],
        ["element_reason", "count"],
    ) + [""]
    excluded = lit_log["case_or_accent_only_differences_excluded"]
    if excluded and not lit_log["allow_case_and_accents"]:
        L += [
            "Of those, spans that differ from the Excel value **only** in case or accents "
            "(would be kept with `LITERAL_ALLOW_CASE_AND_ACCENTS = True` in build_triples.py): "
            + ", ".join(f"{k} = {v}" for k, v in excluded.items())
            + ".",
            "",
        ]

    inferred_by_stmt = {r["stmt_no"]: r for r in join_rows}
    dropped = defaultdict(list)
    for r in lit_join:
        for role in ("attribute", "deontic", "object"):
            reason = r.get(f"{role}_reason", "")
            if reason.startswith("not literal"):
                dropped[(role, reason)].append(
                    {
                        "stmt_no": r["stmt_no"],
                        "excel_value": r[f"{role}_excel"],
                        "inferred_span": inferred_by_stmt[r["stmt_no"]][f"{role}_text"],
                    }
                )
    for (role, reason), rs in sorted(dropped.items(), key=lambda x: -len(x[1])):
        L += details(f"{role}: {reason} ({len(rs)})", md_table(rs, ["stmt_no", "excel_value", "inferred_span"]))
    L += ["Per-row detail: `reports/join_literal.csv`, `reports/edge_cases_literal.csv`.", ""]
    return L


def write_summary(source, filtered, triples, filter_log, join_rows, edge_rows, errors, literal):
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

    L += literal_section(filtered, triples, join_rows, literal)

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

    def read_derived_version(ann_path, id_map_path, jsonl_path):
        with open(id_map_path, encoding="utf-8", newline="") as f:
            tid_map = {int(r["tid"][1:]): int(r["filtered_tid"][1:]) for r in csv.DictReader(f)}
        with open(jsonl_path, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f]
        return read_ann(ann_path), tid_map, rows

    inferred_full_ann, inferred_full_map, inferred_full_jsonl = read_derived_version(
        FULL_ANN_PATH, FULL_ID_MAP_PATH, FULL_JSONL_PATH
    )
    literal_ann, literal_map, literal_jsonl = read_derived_version(
        LITERAL_ANN_PATH, LITERAL_ID_MAP_PATH, LITERAL_JSONL_PATH
    )
    full_ann, full_map, full_jsonl = read_derived_version(
        LITERAL_FULL_ANN_PATH, LITERAL_FULL_ID_MAP_PATH, LITERAL_FULL_JSONL_PATH
    )
    with open(LITERAL_JOIN_CSV_PATH, encoding="utf-8", newline="") as f:
        literal_join = list(csv.DictReader(f))
    with open(LITERAL_LOG_PATH, encoding="utf-8") as f:
        literal_log = json.load(f)

    errors = validate(doc_text, source, filtered, triples, id_map, jsonl_rows)
    inferred_full_name = FULL_ANN_PATH.name
    errors += validate_derived(
        inferred_full_name, doc_text, filtered, inferred_full_ann, inferred_full_map,
        inferred_full_jsonl, exact_spans=True,
    )
    errors += validate_full_triples(inferred_full_name, inferred_full_ann, inferred_full_jsonl)
    errors += validate_literal(doc_text, filtered, literal_ann, literal_map, literal_jsonl)
    full_name = LITERAL_FULL_ANN_PATH.name
    errors += validate_literal(doc_text, filtered, full_ann, full_map, full_jsonl, name=full_name)
    errors += validate_full_triples(full_name, full_ann, full_jsonl)

    with open(VALIDATION_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "passed": not errors,
                "entities_checked": len(triples["entities"]),
                "events_checked": len(triples["events"]),
                "jsonl_rows_checked": len(jsonl_rows),
                "full_entities_checked": len(inferred_full_ann["entities"]),
                "full_events_checked": len(inferred_full_ann["events"]),
                "literal_entities_checked": len(literal_ann["entities"]),
                "literal_events_checked": len(literal_ann["events"]),
                "literal_jsonl_rows_checked": len(literal_jsonl),
                "full_literal_entities_checked": len(full_ann["entities"]),
                "full_literal_events_checked": len(full_ann["events"]),
                "errors": errors,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    literal = {
        "ann": literal_ann,
        "join_rows": literal_join,
        "log": literal_log,
        "full_ann": full_ann,
        "full_jsonl": full_jsonl,
        "inferred_full_ann": inferred_full_ann,
        "inferred_full_jsonl": inferred_full_jsonl,
    }
    write_summary(source, filtered, triples, filter_log, join_rows, edge_rows, errors, literal)

    print(f"Inferred: entities {len(triples['entities'])}, events {len(triples['events'])}, "
          f"jsonl rows {len(jsonl_rows)}")
    print(f"Full triples: entities {len(inferred_full_ann['entities'])}, "
          f"events {len(inferred_full_ann['events'])}")
    print(f"Literal:  entities {len(literal_ann['entities'])}, events {len(literal_ann['events'])}, "
          f"jsonl rows {len(literal_jsonl)}")
    print(f"Full literal triples: entities {len(full_ann['entities'])}, "
          f"events {len(full_ann['events'])}")
    print("Validation PASSED" if not errors else f"Validation FAILED: {len(errors)} errors")
    for e in errors[:20]:
        print(f"  {e}")
    print(f"-> {SUMMARY_MD_PATH}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
