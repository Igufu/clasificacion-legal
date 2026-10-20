"""Stage 1: filter standoff_comp.ann down to Attribute / Deontic / DirectObject.

Drops DirectObjectProperty, IndirectObject, IndirectObjectProperty and every
relation that touches a dropped entity (in this file that is all 28
PropertyOf relations). Offsets and text are copied unchanged; T/R ids are
renumbered consecutively in source order, like merge_literals.py does.

Outputs:
  data/filtered.ann         -- the filtered annotations
  data/filtered.txt         -- copy of document.txt (brat needs a same-name .txt)
  data/filtered_id_map.csv  -- old T id -> new T id, used by build_triples.py
  reports/filter_log.json   -- counts, dropped relations, skipped non-brat lines
"""

import csv
import json
from collections import Counter

from paths import (
    FILTER_LOG_PATH,
    FILTERED_ANN_PATH,
    FILTERED_ID_MAP_PATH,
    FILTERED_TXT_PATH,
    SOURCE_ANN_PATH,
    ensure_outputs_dir,
)
from brat_io import load_document_text, read_ann, t_line, write_doc_copy, write_lines

KEEP_LABELS = ("Attribute", "Deontic", "DirectObject")


def filter_annotations(ann):
    tid_map = {}
    kept = []
    for ent in ann["entities"]:
        if ent["label"] not in KEEP_LABELS:
            continue
        new_tid = len(kept) + 1
        tid_map[ent["tid"]] = new_tid
        kept.append({**ent, "tid": new_tid, "old_tid": ent["tid"]})

    kept_relations, dropped_relations = [], []
    for rel in ann["relations"]:
        if rel["arg1"] in tid_map and rel["arg2"] in tid_map:
            kept_relations.append(
                {
                    **rel,
                    "rid": len(kept_relations) + 1,
                    "arg1": tid_map[rel["arg1"]],
                    "arg2": tid_map[rel["arg2"]],
                }
            )
        else:
            dropped_relations.append(rel)

    if ann["events"] or ann["attributes"]:
        raise NotImplementedError("source has E/A lines; filtering them is not implemented")

    return kept, kept_relations, dropped_relations, tid_map


def check_no_dangling(entities, relations):
    tids = {e["tid"] for e in entities}
    if [e["tid"] for e in entities] != list(range(1, len(entities) + 1)):
        raise AssertionError("T ids are not consecutive")
    if [r["rid"] for r in relations] != list(range(1, len(relations) + 1)):
        raise AssertionError("R ids are not consecutive")
    for r in relations:
        if r["arg1"] not in tids or r["arg2"] not in tids:
            raise AssertionError(f"dangling relation R{r['rid']}")


def main():
    doc_text = load_document_text()
    ann = read_ann(SOURCE_ANN_PATH)
    kept, kept_relations, dropped_relations, tid_map = filter_annotations(ann)
    check_no_dangling(kept, kept_relations)

    for ent in kept:
        if doc_text[ent["start"]:ent["end"]] != ent["text"]:
            raise AssertionError(f"offset/text mismatch at source T{ent['old_tid']}")

    ensure_outputs_dir()
    lines = [t_line(e["tid"], e["label"], e["start"], e["end"], e["text"]) for e in kept]
    lines += [
        f"R{r['rid']}\t{r['label']} Arg1:T{r['arg1']} Arg2:T{r['arg2']}" for r in kept_relations
    ]
    write_lines(FILTERED_ANN_PATH, lines)
    write_doc_copy(doc_text, FILTERED_TXT_PATH)

    with open(FILTERED_ID_MAP_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["old_tid", "new_tid", "label", "start", "end"])
        for e in kept:
            writer.writerow([f"T{e['old_tid']}", f"T{e['tid']}", e["label"], e["start"], e["end"]])

    before = Counter(e["label"] for e in ann["entities"])
    after = Counter(e["label"] for e in kept)
    log = {
        "source": str(SOURCE_ANN_PATH.name),
        "entities_before": dict(before),
        "entities_after": dict(after),
        "relations_before": dict(Counter(r["label"] for r in ann["relations"])),
        "relations_after": dict(Counter(r["label"] for r in kept_relations)),
        "dropped_relations": [
            f"R{r['rid']} {r['label']} Arg1:T{r['arg1']} Arg2:T{r['arg2']}" for r in dropped_relations
        ],
        "skipped_non_brat_lines": [{"line": n, "text": t} for n, t in ann["other"]],
    }
    with open(FILTER_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print(f"Source: {SOURCE_ANN_PATH}")
    print(f"Entities before: {dict(before)}")
    print(f"Entities after:  {dict(after)}")
    print(f"Relations kept: {len(kept_relations)}, dropped: {len(dropped_relations)}")
    print(f"Skipped non-brat lines: {len(ann['other'])}")
    for n, t in ann["other"]:
        print(f"  line {n}: {t!r}")
    print(f"-> {FILTERED_ANN_PATH}")


if __name__ == "__main__":
    main()
