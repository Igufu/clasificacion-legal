"""Central path configuration for the statements pipeline.

Layout:
  <repo>/
    inputs/              raw sources (xml, pdf, xlsx)
    statements/
      scripts/           this file + .py modules
      data/              document.txt, statements.json, triples.*, filtered.*
      reports/           csv/json/md
    visualization/       viz output
"""

import sys
from pathlib import Path

sys.dont_write_bytecode = True

SCRIPTS_DIR  = Path(__file__).resolve().parent
STATEMENTS_DIR = SCRIPTS_DIR.parent
REPO_DIR     = STATEMENTS_DIR.parent

INPUTS_DIR   = REPO_DIR / "inputs"
DATA_DIR     = STATEMENTS_DIR / "data"
REPORTS_DIR  = STATEMENTS_DIR / "reports"
VIZ_DIR      = REPO_DIR / "visualization"

# Inputs
XLSX_PATH    = INPUTS_DIR / "PLAN_INSUMO.xlsx"
RAW_XML_PATH = INPUTS_DIR / "leychile_raw.xml"

# Pipeline artifacts
DOC_TXT_PATH         = DATA_DIR / "document.txt"
STATEMENTS_JSON_PATH = DATA_DIR / "statements.json"

# triples (build_triples.py outputs)
TRIPLES_ANN_PATH   = DATA_DIR / "triples.ann"
TRIPLES_TXT_PATH   = DATA_DIR / "triples.txt"
TRIPLES_JSONL_PATH = DATA_DIR / "triples.jsonl"
JOIN_CSV_PATH       = REPORTS_DIR / "join.csv"
EDGE_CASES_CSV_PATH = REPORTS_DIR / "edge_cases.csv"
LITERACY_JSON_PATH  = REPORTS_DIR / "literacy.json"

# filter_ann.py outputs (standalone utility)
SOURCE_ANN_PATH      = DATA_DIR / "standoff_comp.ann"  # not shipped; kept so filter_ann can still be pointed at one
FILTERED_ANN_PATH    = DATA_DIR / "filtered.ann"
FILTERED_TXT_PATH    = DATA_DIR / "filtered.txt"
FILTERED_ID_MAP_PATH = DATA_DIR / "filtered_id_map.csv"
FILTER_LOG_PATH      = REPORTS_DIR / "filter_log.json"

# validate_report.py outputs
VALIDATION_JSON_PATH = REPORTS_DIR / "validation.json"
SUMMARY_MD_PATH      = REPORTS_DIR / "summary.md"

# visualize_triples.py output
TRIPLES_VIZ_HTML_PATH = VIZ_DIR / "triples_viz.html"

# Legacy placeholders — these point under statements/data/legacy/ and are
# only here so the restored modules (tag_attribute.py, tag_object.py,
# merge_literals.py) import cleanly. Their main() routines are not used by
# the active triples pipeline; only small helpers are consumed.
_LEGACY_DIR = DATA_DIR / "legacy"
ANNOTATIONS_DIR               = _LEGACY_DIR / "annotations"
REVIEW_DIR                    = _LEGACY_DIR / "review"
DOC_ANN_PATH                  = ANNOTATIONS_DIR / "document.ann"
DOC_DEONTIC_LABEL_ANN_PATH    = ANNOTATIONS_DIR / "document_deontic_label.ann"
DEONTIC_LITERAL_ANN_PATH      = ANNOTATIONS_DIR / "deontic_literal.ann"
ATTR_EXPLICIT_ANN_PATH        = ANNOTATIONS_DIR / "attributes_explicit.ann"
ATTR_NORMALIZED_ANN_PATH      = ANNOTATIONS_DIR / "attributes_normalized.ann"
OBJECTS_ANN_PATH              = ANNOTATIONS_DIR / "objects.ann"
TRAINING_LITERALS_ANN_PATH    = ANNOTATIONS_DIR / "training_literals.ann"
UNMATCHED_CSV_PATH            = REVIEW_DIR / "unmatched.csv"
UNMATCHED_STATEMENTS_CSV_PATH = REVIEW_DIR / "unmatched_statements.csv"
UNMATCHED_DEONTIC_CSV_PATH    = REVIEW_DIR / "unmatched_deontic.csv"
ATTR_DIFF_CSV_PATH            = REVIEW_DIR / "attribute_diff.csv"
DEONTIC_DIFF_CSV_PATH         = REVIEW_DIR / "deontic_diff.csv"
UNRESOLVED_OBJECTS_CSV_PATH   = REVIEW_DIR / "unresolved_objects.csv"


def ensure_outputs_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    VIZ_DIR.mkdir(parents=True, exist_ok=True)
