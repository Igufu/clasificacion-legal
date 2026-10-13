"""Central path configuration for the v2_triples pipeline.

Mirrors nlp-tagging/src/paths.py: every I/O location lives here. Importing
this module also puts nlp-tagging/src (and bio_dataset/) on sys.path so the
v2 scripts can reuse the existing parser/matching/tagging code instead of
re-implementing it. Bytecode writing is disabled so importing those modules
never drops __pycache__ files next to the existing sources.
"""

import sys
from pathlib import Path

sys.dont_write_bytecode = True

V2_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = V2_DIR.parent
NLP_SRC_DIR = REPO_DIR / "nlp-tagging" / "src"
BIO_DATASET_DIR = REPO_DIR / "bio_dataset"

for _p in (NLP_SRC_DIR, BIO_DATASET_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from paths import ANNOTATIONS_DIR, DOC_TXT_PATH, XLSX_PATH  # noqa: E402,F401

DATA_DIR = V2_DIR / "data"
REPORTS_DIR = V2_DIR / "reports"

# Input: latest merged annotation file (Attribute/Deontic/objects, literal text).
SOURCE_ANN_PATH = ANNOTATIONS_DIR / "standoff_comp.ann"

# Stage 1 outputs (filter_ann.py)
FILTERED_ANN_PATH = DATA_DIR / "filtered.ann"
FILTERED_TXT_PATH = DATA_DIR / "filtered.txt"
FILTERED_ID_MAP_PATH = DATA_DIR / "filtered_id_map.csv"
FILTER_LOG_PATH = REPORTS_DIR / "filter_log.json"

# Stage 2 outputs (build_triples.py)
TRIPLES_ANN_PATH = DATA_DIR / "triples.ann"
TRIPLES_TXT_PATH = DATA_DIR / "triples.txt"
TRIPLES_JSONL_PATH = DATA_DIR / "triples.jsonl"
JOIN_CSV_PATH = REPORTS_DIR / "join.csv"
EDGE_CASES_CSV_PATH = REPORTS_DIR / "edge_cases.csv"

# Stage 3 outputs (validate_report.py)
VALIDATION_JSON_PATH = REPORTS_DIR / "validation.json"
SUMMARY_MD_PATH = REPORTS_DIR / "summary.md"


def ensure_v2_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
