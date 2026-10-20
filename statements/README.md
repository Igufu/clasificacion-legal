# statements

Per-row literal extraction of Institutional-Grammar triples from
`PLAN_INSUMO.xlsx`, encoded as brat T lines plus three binary relation
types. All inputs sit in `../inputs/`, all intermediate text and brat
files sit in `data/`, all reports in `reports/`, and the HTML viz lives
in `../visualization/`.

## What the pipeline does

For every row of the sheet `DECRETO 31`:

1. Locate the statement's text inside the official document
   (`find_statement_span` from `tag_attribute.py`).
2. For each of the three Excel cells (E = Attribute, G = Deontic,
   I = Direct Object), look up the cell value **literally** inside that
   statement's text (whitespace aside). Bracketed cells (`[Titulares de]
   Buses`, `[deberá]`, …) are implicit by convention and skipped.
3. If the value is found verbatim or after case / Spanish-accent
   folding, emit one brat T line and tag it `tier=verbatim|fuzzy` in the
   jsonl sidecar. If not, the cell is counted in a non-literal ratio and
   no span is written.
4. For every pair of literal spans in the same row, emit a brat binary
   relation. No deontic trigger; no events.

Relation labels:

| label | arg1 | arg2 |
|---|---|---|
| `AttrDeontic`   | Attribute | Deontic |
| `AttrObject`    | Attribute | DirectObject |
| `DeonticObject` | Deontic   | DirectObject |

## Rerun

From the repo root, with the project venv:

```
venv/bin/python statements/scripts/build_triples.py
venv/bin/python statements/scripts/validate_report.py
venv/bin/python visualization/visualize_triples.py
```

`validate_report.py` exits non-zero if any check fails.

`filter_ann.py` is a standalone helper that filters a `standoff_comp.ann`
file down to Attribute / Deontic / DirectObject. The source `.ann` is no
longer shipped (we deleted the old annotation set); point
`paths.SOURCE_ANN_PATH` at a copy if you want to re-run it.

## Inputs (read-only)

| File | Used for |
|---|---|
| `../inputs/PLAN_INSUMO.xlsx`, sheet `DECRETO 31` | Attribute (E), Deontic (G), Direct Object (I) per Statement No. |
| `../inputs/leychile_raw.xml` → `data/document.txt` | Source text; rebuilt from XML on every run and checked equal to `document.txt`. |

## Scripts (`scripts/`)

| File | Job |
|---|---|
| `paths.py` | Central path configuration. |
| `brat_io.py` | brat .ann reader/writer (CRLF-safe); document loader that re-derives the text from `leychile_raw.xml` and asserts it matches `document.txt`. |
| `build_triples.py` | Per-row literal lookup for A/D/O, binary R lines between literal pairs, jsonl sidecar, join / edge-cases CSVs, literacy JSON. |
| `validate_report.py` | T offset/text, id consecutiveness, R endpoint labels, R endpoints on the same statement row, jsonl consistency; writes `summary.md`. |
| `filter_ann.py` | Standalone (not in the triples pipeline). |
| `excel_to_json.py` | Reads `PLAN_INSUMO.xlsx` into `statements.json`. |
| `document_extractor.py` | Rebuilds `document.txt` from `leychile_raw.xml`. |
| `matching.py`, `tag_attribute.py`, `tag_object.py`, `tag_deontic.py`, `merge_literals.py` | Helpers (span location, text normalization, fragment splitting, regex) reused by `build_triples.py`. |

## Outputs

| File | Content |
|---|---|
| `data/triples.ann` (+ `triples.txt`) | T lines (Attribute first, then Deontic, then DirectObject, each in statement order) and R lines. |
| `data/triples.jsonl` | One line per Excel row with any A/D/O cell: cell values, literal/not-literal flag per role, span offsets + T ids when literal, and the R ids attached to the row. |
| `data/filtered.ann` / `filtered.txt` / `filtered_id_map.csv` | Output of `filter_ann.py` (standalone). |
| `data/document.txt` | Source text used by the whole pipeline. |
| `reports/join.csv` | Per Excel row: literal count, relation count, per-role excel/literal/tid/text/reason. |
| `reports/edge_cases.csv` | `non_literal` / `empty_cell` / `multi_value` flags. |
| `reports/literacy.json` | Per-role literal / non-literal counts + non-literal ratio; relation counts; status counts. Read by the HTML. |
| `reports/validation.json`, `reports/summary.md` | Validator log and human-readable summary. |
| `../visualization/triples_viz.html` | Arc diagrams + annotated full text + non-literal ratio banner. |

The `.txt` copies exist because brat needs a same-named text file next
to each `.ann`.
