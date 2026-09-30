"""Central path configuration for the nlp-tagging pipeline.

All I/O locations live here so scripts under src/ never touch each other's
path constants and adding a new artifact only changes one file.
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
INPUTS_DIR = ROOT_DIR / "inputs"
OUTPUTS_DIR = ROOT_DIR / "outputs"

# Outputs are grouped by kind under OUTPUTS_DIR:
#   outputs/               -- pipeline-level artifacts (statements.json, document.txt)
#   outputs/annotations/    -- brat .ann files
#   outputs/review/         -- unmatched/diff CSVs for manual review
ANNOTATIONS_DIR = OUTPUTS_DIR / "annotations"
REVIEW_DIR = OUTPUTS_DIR / "review"

# Inputs
XLSX_PATH = INPUTS_DIR / "PLAN_INSUMO.xlsx"
RAW_XML_PATH = INPUTS_DIR / "leychile_raw.xml"

# Outputs
STATEMENTS_JSON_PATH = OUTPUTS_DIR / "statements.json"
DOC_TXT_PATH = OUTPUTS_DIR / "document.txt"
DOC_ANN_PATH = ANNOTATIONS_DIR / "document.ann"
DOC_DEONTIC_LABEL_ANN_PATH = ANNOTATIONS_DIR / "document_deontic_label.ann"
DEONTIC_LITERAL_ANN_PATH = ANNOTATIONS_DIR / "deontic_literal.ann"
ATTR_EXPLICIT_ANN_PATH = ANNOTATIONS_DIR / "attributes_explicit.ann"
ATTR_NORMALIZED_ANN_PATH = ANNOTATIONS_DIR / "attributes_normalized.ann"
UNMATCHED_CSV_PATH = REVIEW_DIR / "unmatched.csv"
UNMATCHED_STATEMENTS_CSV_PATH = REVIEW_DIR / "unmatched_statements.csv"
UNMATCHED_DEONTIC_CSV_PATH = REVIEW_DIR / "unmatched_deontic.csv"
ATTR_DIFF_CSV_PATH = REVIEW_DIR / "attribute_diff.csv"
DEONTIC_DIFF_CSV_PATH = REVIEW_DIR / "deontic_diff.csv"
OBJECTS_ANN_PATH = ANNOTATIONS_DIR / "objects.ann"
UNRESOLVED_OBJECTS_CSV_PATH = REVIEW_DIR / "unresolved_objects.csv"
TRAINING_LITERALS_ANN_PATH = ANNOTATIONS_DIR / "training_literals.ann"


def ensure_outputs_dir():
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
