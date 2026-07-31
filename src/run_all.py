"""Reproducible full-document extraction driver.

main.py's `chunk N` mode (fixed 24-page slices) proved too coarse for this
model on this document: a wide slice either tripped Gemini's RECITATION
safety filter on dense verbatim tables, or the model silently under-extracted
over a multi-chapter range without erroring at all (finish_reason=STOP but
far fewer statements than the page count warranted). Both failure modes were
found and fixed by hand once (see git history) by re-running smaller
--pages windows and checking the yield. This script automates exactly that
process so it's deterministic and repeatable:

  - Walk the whole document in fixed-size windows (default 8 pages).
  - If a window raises (e.g. RECITATION), halve the window and retry the
    same start page.
  - If a window succeeds but its statements-per-page yield is suspiciously
    low, discard what it appended, halve the window, and retry — this is
    what catches the "no error, just quietly skipped most of the range"
    failure mode.
  - Once a window is at MIN_WINDOW pages, accept whatever it returns (a
    genuinely sparse page — e.g. a page that's just a graphic table with no
    extractable text — should not be retried forever).
  - On success, resume from wherever the accepted window actually ended
    (main.py extends end pages to the next Artículo boundary, so the next
    window's start rarely equals start+window-1).

Because main.py only ever appends to extraction_results.json, this always
starts from an empty file — there's no way to "backfill" fields onto
already-extracted statements in place. Use --fresh to archive whatever is
there now and start clean.

Usage:
    python run_all.py --fresh
    python run_all.py --fresh --window 10 --min-window 2
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import pdfplumber

BASE_DIR = Path(__file__).resolve().parent
DOCUMENT_PDF = BASE_DIR / "data" / "Document_for_processing.pdf"
MAIN_SCRIPT = BASE_DIR / "main.py"
OUTPUT_FILE = BASE_DIR.parent / "output" / "extraction_results.json"

DEFAULT_WINDOW = 8
DEFAULT_MIN_WINDOW = 1
DEFAULT_MIN_YIELD_PER_PAGE = 1.5  # below this, a window is treated as suspect and retried smaller

EXTRACTED_RE = re.compile(r"complete: (\d+) statement\(s\) extracted")
PROCESSING_RE = re.compile(r"processing pages \d+-(\d+) of")


def statement_count():
    if not OUTPUT_FILE.exists():
        return 0
    text = OUTPUT_FILE.read_text(encoding="utf-8").strip()
    return len(json.loads(text)) if text else 0


def truncate_to(n):
    data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
    OUTPUT_FILE.write_text(json.dumps(data[:n], indent=2, ensure_ascii=False), encoding="utf-8")


def archive_existing():
    if not OUTPUT_FILE.exists():
        return
    stamp = time.strftime("%Y%m%d-%H%M%S")
    archive_path = OUTPUT_FILE.with_name(f"extraction_results.pre-{stamp}.json")
    OUTPUT_FILE.rename(archive_path)
    print(f"Archived existing {OUTPUT_FILE.name} -> {archive_path.name}")


def run_range(start, end):
    """Runs `main.py --pages start-end`. Returns (added, actual_end) on a
    clean success, or None on any failure (RECITATION, other API error)."""
    proc = subprocess.run(
        [sys.executable, str(MAIN_SCRIPT), "--pages", f"{start}-{end}"],
        capture_output=True, text=True,
    )
    output = proc.stdout + proc.stderr
    print(output, end="" if output.endswith("\n") else "\n")

    if "ERROR:" in output:
        return None
    match = EXTRACTED_RE.search(output)
    if not match:
        return None
    added = int(match.group(1))
    proc_match = PROCESSING_RE.search(output)
    actual_end = int(proc_match.group(1)) if proc_match else end
    return added, actual_end


def process_document(total_pages, window, min_window, min_yield_per_page):
    start = 1
    current_window = window

    while start <= total_pages:
        end = min(start + current_window - 1, total_pages)
        before = statement_count()
        print(f"\n=== Attempting pages {start}-{end} (window={current_window}) ===")
        outcome = run_range(start, end)

        if outcome is None:
            if current_window <= min_window:
                print(f"WARNING: page {start} failed on its own (see output/debug/); skipping it so the run doesn't stall.")
                start += 1
                current_window = window
                continue
            current_window = max(min_window, current_window // 2)
            print(f"Failed; retrying {start}- with a smaller window ({current_window} pages).")
            continue

        added, actual_end = outcome
        pages_covered = actual_end - start + 1
        yield_ratio = added / pages_covered if pages_covered else 0

        if yield_ratio < min_yield_per_page and current_window > min_window:
            print(f"Low yield ({added} statement(s) / {pages_covered} page(s) = {yield_ratio:.1f}/page) "
                  f"for {start}-{end}; discarding and retrying smaller.")
            truncate_to(before)
            current_window = max(min_window, current_window // 2)
            continue

        print(f"Accepted pages {start}-{actual_end}: {added} statement(s) ({yield_ratio:.1f}/page). "
              f"Total so far: {statement_count()}.")
        start = actual_end + 1
        current_window = window  # back to the default size for the next stretch


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fresh", action="store_true", help="Archive any existing extraction_results.json and start clean. Required unless the file is already absent/empty.")
    parser.add_argument("--window", type=int, default=DEFAULT_WINDOW, help=f"Starting window size in pages (default {DEFAULT_WINDOW}).")
    parser.add_argument("--min-window", type=int, default=DEFAULT_MIN_WINDOW, help=f"Smallest window size to retry down to (default {DEFAULT_MIN_WINDOW}).")
    parser.add_argument("--min-yield-per-page", type=float, default=DEFAULT_MIN_YIELD_PER_PAGE, help=f"Statements-per-page below which a window is treated as suspect (default {DEFAULT_MIN_YIELD_PER_PAGE}).")
    args = parser.parse_args()

    if statement_count() > 0 and not args.fresh:
        sys.exit(f"{OUTPUT_FILE} already has {statement_count()} statement(s). "
                  "Pass --fresh to archive it and start a clean full run (required to backfill any schema/field changes).")
    if args.fresh:
        archive_existing()

    with pdfplumber.open(DOCUMENT_PDF) as pdf:
        total_pages = len(pdf.pages)
    print(f"Document has {total_pages} pages. Starting window={args.window}, min-window={args.min_window}, "
          f"min-yield/page={args.min_yield_per_page}.")

    process_document(total_pages, args.window, args.min_window, args.min_yield_per_page)

    print(f"\nDone: {statement_count()} statement(s) in {OUTPUT_FILE}.")
    print("Regenerating Excel export...")
    subprocess.run([sys.executable, str(BASE_DIR / "json_to_excel.py")], check=True)


if __name__ == "__main__":
    main()

# ./venv/Scripts/python.exe src/run_all.py --fresh