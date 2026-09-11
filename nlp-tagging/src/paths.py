"""Central path configuration for the nlp-tagging pipeline.

All I/O locations live here so scripts under src/ never touch each other's
path constants and adding a new artifact only changes one file.
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
INPUTS_DIR = ROOT_DIR / "inputs"
OUTPUTS_DIR = ROOT_DIR / "outputs"

# Inputs
XLSX_PATH = INPUTS_DIR / "PLAN_INSUMO.xlsx"
RAW_XML_PATH = INPUTS_DIR / "leychile_raw.xml"

# Outputs
STATEMENTS_JSON_PATH = OUTPUTS_DIR / "statements.json"
DOC_TXT_PATH = OUTPUTS_DIR / "document.txt"
DOC_ANN_PATH = OUTPUTS_DIR / "document.ann"
UNMATCHED_CSV_PATH = OUTPUTS_DIR / "unmatched.csv"
UNMATCHED_STATEMENTS_CSV_PATH = OUTPUTS_DIR / "unmatched_statements.csv"
UNMATCHED_DEONTIC_CSV_PATH = OUTPUTS_DIR / "unmatched_deontic.csv"


def ensure_outputs_dir():
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
