"""Convert brat standoff annotations into a CoNLL-2003-style token
classification dataset (words + BIO tags per statement).

Reuses the existing pipeline's in-memory annotation producers rather than
re-parsing the .ann files, because the .ann files don't carry `stmt_no` but
`tag_statements` / `tag_objects` return annotation dicts with it attached.
"""

import csv
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
NLP_SRC = REPO_ROOT / "nlp-tagging" / "src"
sys.path.insert(0, str(NLP_SRC))

from document_extractor import get_document_text  # noqa: E402
from matching import normalize_with_map  # noqa: E402
from paths import STATEMENTS_JSON_PATH  # noqa: E402
from tag_attribute import find_statement_span, tag_statements  # noqa: E402
from tag_object import tag_objects  # noqa: E402


LABELS = [
    "Attribute",
    "Deontic",
    "DirectObject",
    "DirectObjectProperty",
    "IndirectObject",
    "IndirectObjectProperty",
]
LABEL_NAMES = ["O"] + [f"{prefix}-{lbl}" for lbl in LABELS for prefix in ("B", "I")]
LABEL2ID = {name: i for i, name in enumerate(LABEL_NAMES)}

WORD_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)

OUT_DIR = Path(__file__).resolve().parent
DATASET_PATH = OUT_DIR / "dataset.jsonl"
LABEL_NAMES_PATH = OUT_DIR / "label_names.json"
ID2LABEL_PATH = OUT_DIR / "id2label.json"
OVERLAPS_PATH = OUT_DIR / "overlaps.csv"
BOUNDARY_PATH = OUT_DIR / "boundary_issues.csv"
OUT_OF_SPAN_PATH = OUT_DIR / "out_of_span.csv"


def collect_annotations(doc_text, statements):
    """Run the existing taggers and return {stmt_no: [(label, start, end, text)]}."""
    attr_anns, deontic_anns, _, _, _ = tag_statements(doc_text, statements)
    obj_anns_by_label, _, _, _, _ = tag_objects(doc_text, statements)

    by_stmt = {}
    for ann in attr_anns:
        by_stmt.setdefault(ann["stmt_no"], []).append(
            ("Attribute", ann["start"], ann["end"], ann["text"])
        )
    for ann in deontic_anns:
        by_stmt.setdefault(ann["stmt_no"], []).append(
            ("Deontic", ann["start"], ann["end"], ann["text"])
        )
    for label, anns in obj_anns_by_label.items():
        for ann in anns:
            by_stmt.setdefault(ann["stmt_no"], []).append(
                (label, ann["start"], ann["end"], ann["text"])
            )
    return by_stmt


def compute_statement_spans(doc_text, statements):
    """Reproduce the cursor-driven span walk used by tag_statements/tag_objects."""
    doc_norm, doc_norm_map = normalize_with_map(doc_text)
    spans = {}  # stmt_no -> (start, end) or None
    cursor = 0
    for stmt in statements:
        span = find_statement_span(
            doc_text, doc_norm, doc_norm_map, stmt["raw_statement"], cursor
        )
        if span is None:
            spans[stmt["stmt_no"]] = None
            continue
        spans[stmt["stmt_no"]] = span
        cursor = span[1]
    return spans


def report_span_collisions(spans):
    """Count statement pairs whose located doc spans coincide or overlap."""
    items = [(no, s, e) for no, se in spans.items() if se for (no, (s, e)) in [(no, se)]]
    items.sort(key=lambda x: (x[1], x[2]))
    identical_pairs = 0
    overlap_pairs = 0
    stmts_in_identical = set()
    stmts_in_overlap = set()
    for i, (no_i, s_i, e_i) in enumerate(items):
        for no_j, s_j, e_j in items[i + 1:]:
            if s_j >= e_i:
                break
            if s_i == s_j and e_i == e_j:
                identical_pairs += 1
                stmts_in_identical.update({no_i, no_j})
            else:
                overlap_pairs += 1
                stmts_in_overlap.update({no_i, no_j})
    return {
        "identical_pairs": identical_pairs,
        "overlap_pairs": overlap_pairs,
        "stmts_in_identical": len(stmts_in_identical),
        "stmts_in_overlap": len(stmts_in_overlap - stmts_in_identical),
    }


def tokenize_span(doc_text, start, end):
    """Return [(token_text, doc_start, doc_end)] for a span of the document."""
    tokens = []
    for m in WORD_RE.finditer(doc_text, start, end):
        tokens.append((m.group(0), m.start(), m.end()))
    return tokens


def pick_outer(spans_for_word):
    """Pick the 'outer' span: largest (end-start); tie -> earliest start."""
    return max(spans_for_word, key=lambda s: (s[2] - s[1], -s[1]))


def build_example(stmt, stmt_span, stmt_anns, overlaps_log, boundary_log, out_of_span_log):
    """Return (example_dict, applied_anns).

    applied_anns is the set of (label,start,end,text) tuples that actually
    contributed a B- tag; used by the round-trip check.
    """
    stmt_no = stmt["stmt_no"]
    stmt_start, stmt_end = stmt_span

    inside = []
    for ann in stmt_anns:
        label, s, e, text = ann
        if s >= stmt_start and e <= stmt_end:
            inside.append(ann)
        else:
            out_of_span_log.append(
                {
                    "stmt_no": stmt_no,
                    "label": label,
                    "ann_start": s,
                    "ann_end": e,
                    "stmt_start": stmt_start,
                    "stmt_end": stmt_end,
                    "text": text,
                }
            )

    tokens = tokenize_span(doc_text=DOC_TEXT, start=stmt_start, end=stmt_end)
    token_labels = ["O"] * len(tokens)
    applied_first_token = {}  # id(ann_tuple) -> first token index

    for tok_idx, (tok, tok_s, tok_e) in enumerate(tokens):
        matching = []
        for ann in inside:
            label, s, e, _ = ann
            # Token overlaps annotation if they share any characters.
            if tok_s < e and tok_e > s:
                matching.append(ann)
                # Flag boundary cutting through the token (partial word).
                if (s > tok_s and s < tok_e) or (e > tok_s and e < tok_e):
                    boundary_log.append(
                        {
                            "stmt_no": stmt_no,
                            "token": tok,
                            "token_start": tok_s,
                            "token_end": tok_e,
                            "label": label,
                            "ann_start": s,
                            "ann_end": e,
                        }
                    )

        if not matching:
            continue

        if len(matching) > 1:
            overlaps_log.append(
                {
                    "stmt_no": stmt_no,
                    "token": tok,
                    "token_start": tok_s,
                    "token_end": tok_e,
                    "labels": "|".join(a[0] for a in matching),
                    "spans": "|".join(f"{a[1]}-{a[2]}" for a in matching),
                }
            )
            chosen = pick_outer(matching)
        else:
            chosen = matching[0]

        label = chosen[0]
        key = (chosen[0], chosen[1], chosen[2], chosen[3])
        if key not in applied_first_token:
            applied_first_token[key] = tok_idx
            token_labels[tok_idx] = f"B-{label}"
        else:
            token_labels[tok_idx] = f"I-{label}"

    example = {
        "id": stmt_no - 1,
        "statement_no": stmt_no,
        "tokens": [t[0] for t in tokens],
        "ner_tags": [LABEL2ID[lbl] for lbl in token_labels],
        "ner_labels": list(token_labels),
        "token_offsets": [[t[1], t[2]] for t in tokens],
    }
    return example, applied_first_token


def round_trip(example, stmt_anns):
    """Rebuild (label,start,end) triples from BIO tags, compare to stmt_anns.

    Returns (matches, mismatches) where each mismatch is
    (label, start, end, reason).
    """
    tags = [LABEL_NAMES[i] for i in example["ner_tags"]]
    offsets = example["token_offsets"]
    rebuilt = []
    i = 0
    while i < len(tags):
        tag = tags[i]
        if tag == "O":
            i += 1
            continue
        assert tag.startswith("B-"), (tags[i - 1] if i else None, tag)
        label = tag[2:]
        span_start = offsets[i][0]
        span_end = offsets[i][1]
        j = i + 1
        while j < len(tags) and tags[j] == f"I-{label}":
            span_end = offsets[j][1]
            j += 1
        rebuilt.append((label, span_start, span_end))
        i = j

    rebuilt_set = set(rebuilt)
    matches = []
    mismatches = []
    for label, s, e, _text in stmt_anns:
        if (label, s, e) in rebuilt_set:
            matches.append((label, s, e))
        else:
            # Classify why.
            reason = None
            for rl, rs, re_ in rebuilt:
                if rl == label and rs <= s and re_ >= e:
                    reason = "boundary_trim"
                    break
                if rl != label and max(rs, s) < min(re_, e):
                    reason = "overlap"
                    break
            if reason is None:
                reason = "out_of_span_or_missed"
            mismatches.append((label, s, e, reason))
    return matches, mismatches


DOC_TEXT = None  # populated in main; referenced from build_example


def main():
    global DOC_TEXT
    DOC_TEXT = get_document_text()

    with open(STATEMENTS_JSON_PATH, "r", encoding="utf-8") as f:
        statements = json.load(f)
    statements.sort(key=lambda s: s["stmt_no"])

    by_stmt = collect_annotations(DOC_TEXT, statements)
    spans = compute_statement_spans(DOC_TEXT, statements)
    collisions = report_span_collisions(spans)

    overlaps_log = []
    boundary_log = []
    out_of_span_log = []
    examples = []
    round_trip_matches = 0
    round_trip_mismatches = []  # (stmt_no, label, s, e, reason)

    for stmt in statements:
        stmt_no = stmt["stmt_no"]
        span = spans[stmt_no]
        if span is None:
            continue
        stmt_anns = by_stmt.get(stmt_no, [])
        example, _ = build_example(
            stmt, span, stmt_anns, overlaps_log, boundary_log, out_of_span_log
        )
        examples.append(example)

        matches, mismatches = round_trip(example, stmt_anns)
        # Additionally, everything logged as out-of-span for this stmt must be a mismatch.
        oos_keys = {
            (r["label"], r["ann_start"], r["ann_end"])
            for r in out_of_span_log
            if r["stmt_no"] == stmt_no
        }
        already = {(m[0], m[1], m[2]) for m in matches} | {
            (m[0], m[1], m[2]) for m in mismatches
        }
        for label, s, e in oos_keys:
            if (label, s, e) not in already:
                mismatches.append((label, s, e, "out_of_span"))

        round_trip_matches += len(matches)
        for m in mismatches:
            round_trip_mismatches.append((stmt_no, *m))

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(LABEL_NAMES_PATH, "w", encoding="utf-8") as f:
        json.dump(LABEL_NAMES, f, ensure_ascii=False, indent=2)

    with open(ID2LABEL_PATH, "w", encoding="utf-8") as f:
        json.dump({str(i): name for i, name in enumerate(LABEL_NAMES)}, f,
                  ensure_ascii=False, indent=2)

    with open(DATASET_PATH, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    with open(OVERLAPS_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "stmt_no",
                "token",
                "token_start",
                "token_end",
                "labels",
                "spans",
            ],
        )
        w.writeheader()
        w.writerows(overlaps_log)

    with open(BOUNDARY_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "stmt_no",
                "token",
                "token_start",
                "token_end",
                "label",
                "ann_start",
                "ann_end",
            ],
        )
        w.writeheader()
        w.writerows(boundary_log)

    with open(OUT_OF_SPAN_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "stmt_no",
                "label",
                "ann_start",
                "ann_end",
                "stmt_start",
                "stmt_end",
                "text",
            ],
        )
        w.writeheader()
        w.writerows(out_of_span_log)

    total_tokens = sum(len(ex["tokens"]) for ex in examples)
    tag_counts = {name: 0 for name in LABEL_NAMES}
    for ex in examples:
        for t in ex["ner_tags"]:
            tag_counts[LABEL_NAMES[t]] += 1

    mismatch_reason_counts = {}
    for _, _, _, _, reason in round_trip_mismatches:
        mismatch_reason_counts[reason] = mismatch_reason_counts.get(reason, 0) + 1

    print("=" * 60)
    print(f"Statements written: {len(examples)}")
    print(f"Unmatched statement spans (skipped): "
          f"{sum(1 for v in spans.values() if v is None)}")
    print(f"Total tokens: {total_tokens}")
    print()
    print("Statement-span collisions:")
    print(f"  identical span pairs: {collisions['identical_pairs']}")
    print(f"  overlapping (non-identical) pairs: {collisions['overlap_pairs']}")
    print(f"  statements in an identical pair: {collisions['stmts_in_identical']}")
    print(f"  additional statements in an overlap pair: "
          f"{collisions['stmts_in_overlap']}")
    print()
    print("Tag distribution:")
    print(f"  O: {tag_counts['O']}")
    for lbl in LABELS:
        b = tag_counts[f"B-{lbl}"]
        i = tag_counts[f"I-{lbl}"]
        print(f"  {lbl}: B={b}, I={i}, total={b + i}")
    print()
    print(f"Overlap rows logged: {len(overlaps_log)}")
    print(f"Boundary-issue rows logged: {len(boundary_log)}")
    print(f"Out-of-span T-lines logged: {len(out_of_span_log)}")
    print()
    print("Round-trip:")
    print(f"  exact matches: {round_trip_matches}")
    print(f"  mismatches: {len(round_trip_mismatches)}")
    for reason, n in sorted(mismatch_reason_counts.items(), key=lambda x: -x[1]):
        print(f"    {reason}: {n}")

    print()
    print("Sample statements (word\tTAG):")
    sample_ids = [0, len(examples) // 2, len(examples) - 1]
    for idx in sample_ids:
        ex = examples[idx]
        print(f"\n--- statement_no={ex['statement_no']} "
              f"(tokens={len(ex['tokens'])}) ---")
        for tok, tag_id in zip(ex["tokens"], ex["ner_tags"]):
            print(f"{tok}\t{LABEL_NAMES[tag_id]}")


if __name__ == "__main__":
    main()
