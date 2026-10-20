# v2_triples

Per-row literal extraction of Institutional-Grammar triples from
`PLAN_INSUMO.xlsx`, encoded as brat T lines plus three binary relation
types. Nothing under `nlp-tagging/` or `bio_dataset/` is modified; the
v2 scripts only reuse the Excel loader, document loader and matching
helpers from `nlp-tagging/src/`.

## What the pipeline does

For every row of the sheet `DECRETO 31`:

1. Locate the statement's text inside the official document
   (`find_statement_span` from `tag_attribute.py`).
2. For each of the three Excel cells (E = Attribute, G = Deontic,
   I = Direct Object), look up the cell value **literally** inside that
   statement's text (whitespace aside). Bracketed cells (`[Titulares de]
   Buses`, `[deberá]`, …) are implicit by convention and skipped.
3. If the value is found verbatim, emit one brat T line. If not, the
   cell is counted in a non-literal ratio and no span is written.
4. For every pair of literal spans in the same row, emit a brat binary
   relation. No deontic trigger; no events.

Relation labels:

| label | arg1 | arg2 |
|---|---|---|
| `AttrDeontic`   | Attribute | Deontic |
| `AttrObject`    | Attribute | DirectObject |
| `DeonticObject` | Deontic   | DirectObject |

A row with all three literal spans contributes three relations
(`AttrDeontic`, `AttrObject`, `DeonticObject`); a row with just an
Attribute and an Object contributes `AttrObject` alone; a row with only
one literal span contributes that T line and zero R lines.

## Rerun

From the repo root, with the project venv:

```
venv/bin/python v2_triples/scripts/build_triples.py
venv/bin/python v2_triples/scripts/validate_report.py
venv/bin/python v2_triples/scripts/visualize_triples.py
```

`validate_report.py` exits non-zero if any check fails.

`filter_ann.py` is kept as a standalone helper that filters
`standoff_comp.ann` down to Attribute / Deontic / DirectObject, but the
triples pipeline no longer depends on it.

## Inputs (read-only)

| File | Used for |
|---|---|
| `nlp-tagging/inputs/PLAN_INSUMO.xlsx`, sheet `DECRETO 31` | Attribute (E), Deontic (G), Direct Object (I) per Statement No. |
| `nlp-tagging/inputs/leychile_raw.xml` / `nlp-tagging/outputs/document.txt` | source text; rebuilt from XML and checked equal to `document.txt` (never rewritten) |

## Scripts

| File | Job |
|---|---|
| `v2_paths.py` | All v2 paths; puts `nlp-tagging/src` and `bio_dataset` on `sys.path`; prunes legacy event-based outputs on each run. |
| `brat_io.py` | .ann reader/writer (reuses the regexes from `merge_literals.py`, CRLF-safe); document loader. |
| `build_triples.py` | Per-row literal lookup for A/D/O, binary R lines between literal pairs, jsonl sidecar, join / edge-cases CSVs, literacy JSON. |
| `validate_report.py` | T offset/text, id consecutiveness, R endpoint labels, R endpoints on the same statement row, jsonl consistency; writes `summary.md`. |
| `visualize_triples.py` | One HTML page: non-literal ratio cards, one row card per non-empty Excel row (arc diagram + per-role details), full annotated text. |
| `filter_ann.py` | Standalone (not in the triples pipeline): filter `standoff_comp.ann` down to Attribute / Deontic / DirectObject. |

## Outputs

| File | Content |
|---|---|
| `data/triples.ann` (+ `triples.txt`) | T lines (Attribute first, then Deontic, then DirectObject, each in statement order) and R lines (binary relations). |
| `data/triples.jsonl` | One line per Excel row with any A/D/O cell: cell values, literal/not-literal flag per role, span offsets + T ids when literal, and the R ids attached to the row. |
| `reports/join.csv` | Per Excel row: literal count, relation count, per-role excel/literal/tid/text/reason. |
| `reports/edge_cases.csv` | `non_literal` (dropped), `empty_cell`, `multi_value` flags. |
| `reports/literacy.json` | Per-role literal / non-literal counts + non-literal ratio; relation counts; status counts. Read by the HTML. |
| `reports/validation.json`, `reports/summary.md` | Validator log and human-readable summary. |
| `reports/triples_viz.html` | Row cards (arc diagrams) + annotated full text + non-literal ratio banner. |

The `.txt` copy exists because brat needs a same-named text file next
to each `.ann`.
