# v2_triples

Direct-Object-only version of the annotations plus Attribute–Deontic–Object
triples. Everything here is new; nothing under `nlp-tagging/` or
`bio_dataset/` is modified. The scripts import the existing code from
`nlp-tagging/src/` (matching, Excel loader, taggers) and `bio_dataset/`
(statement-span walk) instead of re-implementing it.

## Rerun the pipeline

From the repo root, with the project venv:

```
venv/Scripts/python.exe v2_triples/scripts/filter_ann.py
venv/Scripts/python.exe v2_triples/scripts/build_triples.py
venv/Scripts/python.exe v2_triples/scripts/validate_report.py
```

Each step reads only the previous step's outputs plus the existing inputs.
`validate_report.py` exits non-zero if any check fails.

## Inputs (existing, read-only)

| File | Used for |
|---|---|
| `nlp-tagging/outputs/annotations/standoff_comp.ann` | source spans (latest merged file, literal text) |
| `nlp-tagging/inputs/PLAN_INSUMO.xlsx`, sheet `DECRETO 31` | Attribute (E), Deontic (G), Direct Object (I) per Statement No. |
| `nlp-tagging/inputs/leychile_raw.xml` / `nlp-tagging/outputs/document.txt` | source text; rebuilt from XML and checked equal to `document.txt` (never rewritten) |

## Scripts (`scripts/`)

| File | Job |
|---|---|
| `v2_paths.py` | All v2 paths; puts `nlp-tagging/src` and `bio_dataset` on `sys.path`; disables `__pycache__` writes. |
| `brat_io.py` | .ann reader/writer (reuses `merge_literals.TLINE_RE/RLINE_RE`, CRLF-safe, reports non-brat lines); document loader. |
| `filter_ann.py` | Step 2: keep Attribute / Deontic / DirectObject, drop the rest and every relation touching a dropped entity, renumber ids, check no dangling refs. |
| `build_triples.py` | Step 3: join Excel rows to T ids (re-runs the existing taggers and asserts they reproduce `standoff_comp.ann` exactly, so each T inherits its `stmt_no`), write one brat event per Deontic span, the jsonl sidecar, and flag edge cases. |
| `validate_report.py` | Step 4: offset/text, id, event and jsonl checks; writes `summary.md`. |

## Outputs

| File | Content |
|---|---|
| `data/filtered.ann` (+ `filtered.txt`) | Step 2 result: T lines only (no relations survive). |
| `data/filtered_id_map.csv` | source T id → new T id. |
| `data/triples.ann` (+ `triples.txt`) | same T lines as `filtered.ann` + events `E{n}\tDeontic:T{d} Attribute:T{a} Object:T{o}` (args omitted when that span is missing). |
| `data/triples.jsonl` | one line per Excel row with any A/D/O value: `statement_no, attribute_text, attribute_span, deontic, object_text, object_span` + ids, Excel values, status, missing reasons. |
| `reports/join.csv` | per Excel row: linked T ids/text or the reason it could not be linked. |
| `reports/edge_cases.csv` | every flagged case (multi-value, empty, bracketed, unmatched, partial, cross-reference, shared span). |
| `reports/filter_log.json`, `reports/validation.json` | step logs. |
| `reports/summary.md` | counts before/after, triple counts, unmatched rows, flagged edge cases. |

The `.txt` copies exist because brat needs a same-named text file next to each `.ann`.
