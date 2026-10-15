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
venv/Scripts/python.exe v2_triples/scripts/visualize_triples.py
```

Each step reads only the previous step's outputs plus the existing inputs.
`validate_report.py` exits non-zero if any check fails.

## Two versions: inferred vs. literal

`build_triples.py` writes both from the same join:

- **inferred** (`triples.*`): every span the existing matchers found. That
  includes spans "translated" from a non-literal Excel value: bracketed values
  (`[Titulares de] Buses` → `buses`, `[deberá]` → `generará`),
  cross-references to an earlier sentence, and case/accent-folded matches.
  The Deontic is the bold surface phrase (`deberán contar`).
- **literal** (`triples_literal.*`): only spans whose text **is** the Excel
  cell value (only whitespace may differ), inside the statement's own text.
  Bracketed cells are never literal. The Deontic is narrowed to the Excel
  modal as a whole word inside the bold phrase (`deberán contar` → `deberán`).
  No new matching is done; literal spans are a subset/narrowing of the inferred
  ones. `LITERAL_ALLOW_CASE_AND_ACCENTS` in `build_triples.py` (default
  `False`) also accepts case/accent-only differences (`Buses`/`buses`).

- **full triples** (`triples_full.*`): the inferred version restricted to
  statements with an Attribute, Deontic **and** Object span (spans may still
  be inferred). Every event is a complete triple.
- **full literal triples** (`triples_literal_full.*`): the literal version
  restricted to statements whose Attribute, Deontic **and** Object are all
  literal. Every event is a complete triple and every span belongs to one.

The visualization has a toggle at the top to switch between the four. In the
full-text view, spans that belong to no event (their statement has no Deontic
span in that version) carry a dashed `no deontic · St. N` chip.

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
| `build_triples.py` | Step 3: join Excel rows to T ids (re-runs the existing taggers and asserts they reproduce `standoff_comp.ann` exactly, so each T inherits its `stmt_no`), write one brat event per Deontic span, the jsonl sidecar, and flag edge cases, for all four versions (inferred, full triples, literal, full literal triples). |
| `validate_report.py` | Step 4: offset/text, id, event and jsonl checks for all four versions (literal: every span must come from an inferred span and equal its Excel value; full versions: every event complete, every span in an event); writes `summary.md`. |
| `visualize_triples.py` | Event cards (arc diagrams) + annotated full text for the four versions in one HTML, with a toggle. |

## Outputs

| File | Content |
|---|---|
| `data/filtered.ann` (+ `filtered.txt`) | Step 2 result: T lines only (no relations survive). |
| `data/filtered_id_map.csv` | source T id → new T id. |
| `data/triples.ann` (+ `triples.txt`) | same T lines as `filtered.ann` + events `E{n}\tDeontic:T{d} Attribute:T{a} Object:T{o}` (args omitted when that span is missing). |
| `data/triples.jsonl` | one line per Excel row with any A/D/O value: `statement_no, attribute_text, attribute_span, deontic, object_text, object_span` + ids, Excel values, status, missing reasons. |
| `reports/join.csv` | per Excel row: linked T ids/text or the reason it could not be linked. |
| `reports/edge_cases.csv` | every flagged case (multi-value, empty, bracketed, unmatched, partial, cross-reference, shared span). |
| `data/triples_literal.ann` (+ `.txt`), `data/triples_literal.jsonl` | literal-only version, same formats (own T/E numbering). |
| `data/literal_id_map.csv` | literal T id (`tid`) → the `filtered.ann` T it came from (`narrowed` = Deontic cut down to the modal). |
| `reports/join_literal.csv`, `reports/edge_cases_literal.csv` | same as above for the literal version; reasons start with `not literal:` when an inferred span was dropped. |
| `data/triples_full.ann` (+ `.txt`), `data/triples_full.jsonl`, `data/full_id_map.csv`, `reports/join_full.csv`, `reports/edge_cases_full.csv` | full-triples version (inferred, complete only), same formats. |
| `data/triples_literal_full.ann` (+ `.txt`), `data/triples_literal_full.jsonl`, `data/literal_full_id_map.csv`, `reports/join_literal_full.csv`, `reports/edge_cases_literal_full.csv` | full-literal-triples version, same formats. |
| `reports/filter_log.json`, `reports/literal_log.json`, `reports/validation.json` | step logs. |
| `reports/summary.md` | counts before/after, triple counts, inferred vs. literal comparison, unmatched rows, flagged edge cases. |
| `reports/triples_viz.html` | visualization with the inferred / literal toggle. |

The `.txt` copies exist because brat needs a same-named text file next to each `.ann`.
