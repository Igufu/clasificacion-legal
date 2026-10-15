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

# Stage 2 full-triples outputs (build_triples.py): the inferred version
# restricted to statements with an Attribute, Deontic AND Object span.
FULL_ANN_PATH = DATA_DIR / "triples_full.ann"
FULL_TXT_PATH = DATA_DIR / "triples_full.txt"
FULL_JSONL_PATH = DATA_DIR / "triples_full.jsonl"
FULL_ID_MAP_PATH = DATA_DIR / "full_id_map.csv"
FULL_JOIN_CSV_PATH = REPORTS_DIR / "join_full.csv"
FULL_EDGE_CASES_CSV_PATH = REPORTS_DIR / "edge_cases_full.csv"

# Stage 2 literal-only outputs (build_triples.py): only spans whose text is
# the Excel value itself, found in the statement's own text.
LITERAL_ANN_PATH = DATA_DIR / "triples_literal.ann"
LITERAL_TXT_PATH = DATA_DIR / "triples_literal.txt"
LITERAL_JSONL_PATH = DATA_DIR / "triples_literal.jsonl"
LITERAL_ID_MAP_PATH = DATA_DIR / "literal_id_map.csv"
LITERAL_JOIN_CSV_PATH = REPORTS_DIR / "join_literal.csv"
LITERAL_EDGE_CASES_CSV_PATH = REPORTS_DIR / "edge_cases_literal.csv"
LITERAL_LOG_PATH = REPORTS_DIR / "literal_log.json"

# Stage 2 full-literal-triples outputs (build_triples.py): the literal
# version restricted to statements whose Attribute, Deontic AND Object are
# all literal.
LITERAL_FULL_ANN_PATH = DATA_DIR / "triples_literal_full.ann"
LITERAL_FULL_TXT_PATH = DATA_DIR / "triples_literal_full.txt"
LITERAL_FULL_JSONL_PATH = DATA_DIR / "triples_literal_full.jsonl"
LITERAL_FULL_ID_MAP_PATH = DATA_DIR / "literal_full_id_map.csv"
LITERAL_FULL_JOIN_CSV_PATH = REPORTS_DIR / "join_literal_full.csv"
LITERAL_FULL_EDGE_CASES_CSV_PATH = REPORTS_DIR / "edge_cases_literal_full.csv"

# Stage 3 outputs (validate_report.py)
VALIDATION_JSON_PATH = REPORTS_DIR / "validation.json"
SUMMARY_MD_PATH = REPORTS_DIR / "summary.md"

# Visualization (visualize_triples.py)
TRIPLES_VIZ_HTML_PATH = REPORTS_DIR / "triples_viz.html"


def ensure_v2_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
