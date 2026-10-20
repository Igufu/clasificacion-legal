"""Central path configuration for the v2_triples pipeline.

Also puts nlp-tagging/src and bio_dataset on sys.path so the v2 scripts can
reuse the existing document/matching helpers, and disables bytecode writes
so importing those modules never drops __pycache__ files next to them.
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

# Latest merged source .ann (kept for filter_ann.py, no longer part of the
# triples pipeline — build_triples.py reads from the Excel directly).
SOURCE_ANN_PATH = ANNOTATIONS_DIR / "standoff_comp.ann"

# filter_ann.py outputs (standalone utility; triples don't depend on them)
FILTERED_ANN_PATH = DATA_DIR / "filtered.ann"
FILTERED_TXT_PATH = DATA_DIR / "filtered.txt"
FILTERED_ID_MAP_PATH = DATA_DIR / "filtered_id_map.csv"
FILTER_LOG_PATH = REPORTS_DIR / "filter_log.json"

# build_triples.py outputs
TRIPLES_ANN_PATH   = DATA_DIR / "triples.ann"
TRIPLES_TXT_PATH   = DATA_DIR / "triples.txt"
TRIPLES_JSONL_PATH = DATA_DIR / "triples.jsonl"
JOIN_CSV_PATH         = REPORTS_DIR / "join.csv"
EDGE_CASES_CSV_PATH   = REPORTS_DIR / "edge_cases.csv"
LITERACY_JSON_PATH    = REPORTS_DIR / "literacy.json"

# validate_report.py outputs
VALIDATION_JSON_PATH = REPORTS_DIR / "validation.json"
SUMMARY_MD_PATH      = REPORTS_DIR / "summary.md"

# visualize_triples.py output
TRIPLES_VIZ_HTML_PATH = REPORTS_DIR / "triples_viz.html"

# Legacy outputs removed when the pipeline switched from events to binary
# relations; prune_legacy_outputs() deletes them so stale copies don't
# confuse readers.
_LEGACY_PATHS = [
    DATA_DIR / "triples_full.ann",
    DATA_DIR / "triples_full.txt",
    DATA_DIR / "triples_full.jsonl",
    DATA_DIR / "triples_literal.ann",
    DATA_DIR / "triples_literal.txt",
    DATA_DIR / "triples_literal.jsonl",
    DATA_DIR / "triples_literal_full.ann",
    DATA_DIR / "triples_literal_full.txt",
    DATA_DIR / "triples_literal_full.jsonl",
    DATA_DIR / "full_id_map.csv",
    DATA_DIR / "literal_id_map.csv",
    DATA_DIR / "literal_full_id_map.csv",
    REPORTS_DIR / "join_full.csv",
    REPORTS_DIR / "join_literal.csv",
    REPORTS_DIR / "join_literal_full.csv",
    REPORTS_DIR / "edge_cases_full.csv",
    REPORTS_DIR / "edge_cases_literal.csv",
    REPORTS_DIR / "edge_cases_literal_full.csv",
    REPORTS_DIR / "literal_log.json",
]


def ensure_v2_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def prune_legacy_outputs():
    for p in _LEGACY_PATHS:
        if p.exists():
            p.unlink()
