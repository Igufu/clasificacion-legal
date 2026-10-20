"""Validate triples.ann / triples.jsonl / literacy.json and write
reports/summary.md.

Checks:
  - every T line: document.txt[start:end] == text, no newline, label in
    {Attribute, Deontic, DirectObject}.
  - T and R ids consecutive; no unparsed lines; no dangling references.
  - every R line is a binary relation whose arg labels match its own
    (AttrDeontic -> Attribute+Deontic, AttrObject -> Attribute+DirectObject,
    DeonticObject -> Deontic+DirectObject), both args point at T lines
    created from the same statement row (via the jsonl sidecar).
  - the jsonl rows agree with the .ann for every span and every relation
    they declare, and every row with a literal span has a T id for it.

Writes:
  reports/validation.json
  reports/summary.md
"""

import csv
import json
import sys
from collections import Counter, defaultdict

from paths import (
    EDGE_CASES_CSV_PATH,
    JOIN_CSV_PATH,
    LITERACY_JSON_PATH,
    SUMMARY_MD_PATH,
    TRIPLES_ANN_PATH,
    TRIPLES_JSONL_PATH,
    VALIDATION_JSON_PATH,
)
from brat_io import load_document_text, read_ann

KEEP_LABELS = ("Attribute", "Deontic", "DirectObject")
RELATION_ARG_LABELS = {
    "AttrDeontic":   ("Attribute", "Deontic"),
    "AttrObject":    ("Attribute", "DirectObject"),
    "DeonticObject": ("Deontic",  "DirectObject"),
}
ROLE_ORDER = ("attribute", "deontic", "object")


def check_ann(ann, doc_text):
    errors = []
    if ann["other"]:
        errors.append(f"{len(ann['other'])} unparsed lines")
    if ann["events"] or ann["attributes"]:
        errors.append("unexpected E/A lines (binary-relation version has only T/R)")
    tids = [e["tid"] for e in ann["entities"]]
    if tids != list(range(1, len(tids) + 1)):
        errors.append("T ids are not consecutive")
    rids = [r["rid"] for r in ann["relations"]]
    if rids != list(range(1, len(rids) + 1)):
        errors.append("R ids are not consecutive")

    tid_label = {}
    for e in ann["entities"]:
        tid_label[e["tid"]] = e["label"]
        if e["label"] not in KEEP_LABELS:
            errors.append(f"T{e['tid']}: label {e['label']} not in {KEEP_LABELS}")
        if "\n" in e["text"] or "\r" in e["text"]:
            errors.append(f"T{e['tid']}: text contains a newline")
        if doc_text[e["start"]:e["end"]] != e["text"]:
            errors.append(
                f"T{e['tid']}: doc[{e['start']}:{e['end']}]="
                f"{doc_text[e['start']:e['end']]!r} != {e['text']!r}"
            )

    for r in ann["relations"]:
        expected = RELATION_ARG_LABELS.get(r["label"])
        if expected is None:
            errors.append(f"R{r['rid']}: unknown label {r['label']}")
            continue
        got = (tid_label.get(r["arg1"]), tid_label.get(r["arg2"]))
        if got != expected:
            errors.append(
                f"R{r['rid']} {r['label']}: arg labels {got} != expected {expected}"
            )
    return errors


def check_jsonl(ann, jsonl_rows):
    errors = []
    ents = {e["tid"]: e for e in ann["entities"]}
    rels = {r["rid"]: r for r in ann["relations"]}

    stmt_of_tid = {}
    for row in jsonl_rows:
        n = row["statement_no"]
        for role in ROLE_ORDER:
            tid = row[f"{role}_tid"]
            if tid is None:
                continue
            e = ents.get(int(tid[1:]))
            if e is None:
                errors.append(f"stmt {n}: {role} tid {tid} missing from .ann")
                continue
            if row[f"{role}_span"] != [e["start"], e["end"]] or row[f"{role}_text"] != e["text"]:
                errors.append(f"stmt {n}: {role} span/text differs from .ann")
            stmt_of_tid[int(tid[1:])] = n

    # Every T must be claimed by exactly one jsonl row.
    unclaimed = sorted(set(ents) - set(stmt_of_tid))
    if unclaimed:
        errors.append(f"T lines not referenced by any jsonl row: {unclaimed[:5]}... ({len(unclaimed)} total)")

    # Every R endpoint must come from the same statement row.
    for row in jsonl_rows:
        for rel in row.get("relations", []):
            r = rels.get(int(rel["rid"][1:]))
            if r is None:
                errors.append(f"stmt {row['statement_no']}: {rel['rid']} missing from .ann")
                continue
            if f"T{r['arg1']}" != rel["arg1"] or f"T{r['arg2']}" != rel["arg2"]:
                errors.append(f"stmt {row['statement_no']}: {rel['rid']} args mismatch")
            if stmt_of_tid.get(r["arg1"]) != row["statement_no"] or stmt_of_tid.get(r["arg2"]) != row["statement_no"]:
                errors.append(f"stmt {row['statement_no']}: {rel['rid']} crosses statement boundary")
    return errors


def md_table(rows, cols):
    def cell(v):
        return str(v).replace("|", "\\|").replace("\n", " ")
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(cell(r.get(c, "")) for c in cols) + " |" for r in rows]
    return out


def details(title, lines):
    return ["<details>", f"<summary>{title}</summary>", ""] + lines + ["", "</details>", ""]


def write_summary(ann, jsonl_rows, join_rows, edge_rows, literacy, errors):
    status = Counter(r["status"] for r in join_rows)
    rel_by_label = Counter(r["label"] for r in ann["relations"])
    entity_by_label = Counter(e["label"] for e in ann["entities"])

    L = ["# v2_triples summary", ""]
    L += [
        "Each Excel row is mapped to the statement it describes; its Attribute, "
        "Deontic and Direct Object cells are looked up in the statement's own "
        "text, allowing whitespace / case / Spanish accent differences "
        "(so Excel `amoniaco` matches `amoníaco`). Bracketed cells "
        "(`[Titulares de] Buses`, `[deberá]`, …) are implicit by convention "
        "and skipped. Any cell that still can't be found is dropped and "
        "counted in the non-literal ratio below. There is no event trigger: "
        "every pair of literal spans in the same row becomes one brat binary "
        "relation (AttrDeontic, AttrObject, DeonticObject).",
        "",
        f"**Validation: {'PASSED' if not errors else f'FAILED ({len(errors)} errors)'}**",
        "",
    ]
    if errors:
        L += ["## Validation errors", ""] + [f"- {e}" for e in errors] + [""]

    L += ["## Row outcomes", ""]
    L += md_table(
        [
            {"status": "complete (A + D + O literal, 3 relations)", "rows": status.get("complete", 0)},
            {"status": "pair (2 literal roles, 1 relation)",         "rows": status.get("pair", 0)},
            {"status": "single (1 literal role, 0 relations)",       "rows": status.get("single", 0)},
            {"status": "no literal span (row kept text, no spans)",  "rows": status.get("no_literal_span", 0)},
            {"status": "all three cells empty (skipped)",             "rows": status.get("all_cells_empty", 0)},
            {"status": "**Excel rows total**",                        "rows": len(join_rows)},
        ],
        ["status", "rows"],
    ) + [""]

    L += ["## Literal vs. non-literal per role", ""]
    L += [
        "A cell is **non-literal** when it is bracketed (implicit value) or "
        "when it is non-bracketed but doesn't appear in the statement's text "
        "even after whitespace / case / accent folding. Empty cells are "
        "excluded from the ratio.",
        "",
    ]
    L += md_table(
        [
            {
                "role": role_data["label"],
                "with value": role_data["with_value"],
                "literal": role_data["literal"],
                "non-literal": role_data["non_literal"],
                "non-literal ratio": f"{role_data['non_literal_ratio']:.1%}" if role_data["with_value"] else "n/a",
                "empty cells": role_data["empty"],
            }
            for role in ROLE_ORDER
            for role_data in [literacy["roles"][role]]
        ],
        ["role", "with value", "literal", "non-literal", "non-literal ratio", "empty cells"],
    ) + [""]

    L += ["## Spans and relations written", ""]
    rows = [
        {"kind": lbl, "count": entity_by_label.get(lbl, 0)}
        for lbl in KEEP_LABELS
    ]
    rows.append({"kind": "**T total**", "count": len(ann["entities"])})
    for label in RELATION_ARG_LABELS:
        rows.append({"kind": f"R {label}", "count": rel_by_label.get(label, 0)})
    rows.append({"kind": "**R total**", "count": len(ann["relations"])})
    L += md_table(rows, ["kind", "count"]) + [""]

    L += ["## Non-literal rows", ""]
    L += [
        "Non-bracketed Excel cells that still don't appear literally in the "
        "statement text, grouped by role. Full per-row detail: "
        "`reports/join.csv`, `reports/edge_cases.csv`.",
        "",
    ]
    missed = defaultdict(list)
    for row in jsonl_rows:
        for role in ROLE_ORDER:
            excel = row[f"{role}_excel"]
            if excel is None or "[" in excel:
                continue
            if row[f"{role}_literal"]:
                continue
            missed[role].append({
                "stmt_no": row["statement_no"],
                "excel_value": excel,
            })
    for role in ROLE_ORDER:
        rs = missed[role]
        if not rs:
            continue
        L += details(f"{role} ({len(rs)})", md_table(rs, ["stmt_no", "excel_value"]))

    L += ["## Bracketed (implicit) rows", ""]
    L += [
        "Bracketed Excel values are implicit by convention and never considered "
        "literal; counted here for reference.",
        "",
    ]
    bracketed = defaultdict(list)
    for row in jsonl_rows:
        for role in ROLE_ORDER:
            excel = row[f"{role}_excel"]
            if excel and "[" in excel:
                bracketed[role].append({"stmt_no": row["statement_no"], "excel_value": excel})
    for role in ROLE_ORDER:
        rs = bracketed[role]
        if not rs:
            continue
        L += details(f"{role} ({len(rs)})", md_table(rs, ["stmt_no", "excel_value"]))

    L += ["## Multi-value cells", "",
          "Rows whose Excel cell holds several items separated by `;` / newline / `[AND]` / `[OR]`. "
          "Not split (no cross product): the row contributes at most one T per role.", ""]
    multi = [r for r in edge_rows if r["kind"] == "multi_value"]
    if multi:
        L += details(
            f"multi-value rows ({len(multi)})",
            md_table(multi, ["stmt_no", "element", "excel_value", "note"]),
        )

    with open(SUMMARY_MD_PATH, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(L) + "\n")


def main():
    doc_text = load_document_text()
    ann = read_ann(TRIPLES_ANN_PATH)
    with open(TRIPLES_JSONL_PATH, encoding="utf-8") as f:
        jsonl_rows = [json.loads(line) for line in f]
    with open(JOIN_CSV_PATH, encoding="utf-8", newline="") as f:
        join_rows = list(csv.DictReader(f))
    with open(EDGE_CASES_CSV_PATH, encoding="utf-8", newline="") as f:
        edge_rows = list(csv.DictReader(f))
    with open(LITERACY_JSON_PATH, encoding="utf-8") as f:
        literacy = json.load(f)

    errors = check_ann(ann, doc_text) + check_jsonl(ann, jsonl_rows)

    with open(VALIDATION_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "passed": not errors,
                "entities": len(ann["entities"]),
                "relations": len(ann["relations"]),
                "jsonl_rows": len(jsonl_rows),
                "errors": errors,
            },
            f, ensure_ascii=False, indent=2,
        )

    write_summary(ann, jsonl_rows, join_rows, edge_rows, literacy, errors)

    print(f"Entities: {len(ann['entities'])}, relations: {len(ann['relations'])}, "
          f"jsonl rows: {len(jsonl_rows)}")
    print("Validation PASSED" if not errors else f"Validation FAILED: {len(errors)} errors")
    for e in errors[:20]:
        print(f"  {e}")
    print(f"-> {SUMMARY_MD_PATH}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
