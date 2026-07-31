import argparse
import difflib
import json
import re
import sys
import time
from collections import deque
from pathlib import Path
from dotenv import load_dotenv
import pdfplumber
from google import genai
from google.genai import types

from prompt_builder import (
    build_base_prompt,
    build_batch_prompt,
    build_categories_prompt,
    build_response_schema,
    clean_json_response,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR.parent / "output"
DEBUG_DIR = OUTPUT_DIR / "debug"

MODEL = "gemini-3.1-flash-lite"
PAGES_PER_BATCH = 8
PAGES_PER_CHUNK = 24  # pages processed per CLI invocation; chunk N = pages ((N-1)*PAGES_PER_CHUNK+1)-(N*PAGES_PER_CHUNK)
MAX_RETRIES = 4
RETRY_BACKOFF_SECONDS = 5
MAX_OUTPUT_TOKENS = 65536

# Retries escalate temperature — 0.0 alone just resends an identical request,
# which tends to hit the same RECITATION wall again. RECITATION has no
# dedicated safety_settings knob in the API; temperature is the only lever
# that actually changes the odds, so the last attempt goes noticeably higher
# than the rest as a final push before giving up. Once MAX_RETRIES is
# exhausted the page range is halved and each half gets its own fresh retry
# budget: a smaller verbatim span is less likely to trip RECITATION at all.
RETRY_TEMPERATURES = [0.0, 0.2, 0.4, 0.7]
MIN_BATCH_PAGES = 1

# Statement No. is assigned by renumber_batch, never trusted from the model:
# each batch is an independent call with no memory of prior batches' counts,
# so model-assigned numbers reset to 1 every batch. These fields carry a
# Statement No. cross-reference and get shifted by the same offset.
REFERENCE_FIELDS = [
    "Invoking statement(s)",
    "Direct Object (Reference to statement)",
    "Indirect Object (Reference to statement)",
    "Activation Condition (Reference to statement)",
    "Execution Constraint (Reference to statement)",
    "Or else (Forward reference)",
]

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def renumber_batch(batch_results, offset):
    """Assigns globally sequential Statement No. values — each batch's own
    numbering restarts at 1 — and shifts same-batch reference fields (e.g.
    "Invoking statement(s)") by the same offset so they still point at the
    right statement. The "0" placeholder (= no second reference) is left alone."""
    def shift(value):
        return re.sub(r"\d+", lambda m: m.group() if m.group() == "0" else str(int(m.group()) + offset), value)

    for i, statement in enumerate(batch_results, start=1):
        statement["Statement No."] = str(offset + i)
        for field in REFERENCE_FIELDS:
            value = statement.get(field)
            if value and str(value).strip():
                statement[field] = shift(str(value))
    return batch_results


def check_bare_table_titles(statements):
    """Flags statements whose entire Raw Statement is just a table title with
    no governing sentence — MERGING CONVENTION requires the table name to be
    folded into the introducing statement instead."""
    pattern = re.compile(r"^\s*\[?\s*Tabla\s+[\w.-]+\s*:.*\]?\s*$", re.IGNORECASE)
    flagged = [s for s in statements if pattern.match(s.get("Raw Statement", ""))]
    if flagged:
        print(f"WARNING: {len(flagged)} statement(s) look like a bare table title with no governing sentence:")
        for s in flagged:
            print(f"  - [{s.get('Statement No.')}] {s.get('Raw Statement', '')[:80]}")
    else:
        print("Table-merging check passed: no statement is a bare table title.")


def save_progress(statements, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(statements, f, indent=2, ensure_ascii=False)


def extract_batch(client, contents, categories_prompt, response_schema, temperature=0.0):
    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=categories_prompt,
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=response_schema,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        ),
    )

    if response.candidates:
        finish_reason = response.candidates[0].finish_reason
        if finish_reason not in (types.FinishReason.STOP, None):
            raise RuntimeError(f"Generation did not finish cleanly (finish_reason={finish_reason})")

    clean_text = clean_json_response(response.text)
    results = json.loads(clean_text)
    return results if isinstance(results, list) else [results]


def process_page_range(client, base_prompt, document, guideline, aux_guideline,
                        categories_prompt, response_schema, start_page, end_page, total_pages):
    """Runs one page range through MAX_RETRIES attempts with escalating
    temperature. Returns (results, None) on success, or (None, error) once
    every attempt at this granularity has failed."""
    batch_prompt = build_batch_prompt(base_prompt, start_page, end_page, total_pages)
    contents = [document, guideline, aux_guideline, batch_prompt]

    error = None
    for attempt in range(1, MAX_RETRIES + 1):
        temperature = RETRY_TEMPERATURES[min(attempt - 1, len(RETRY_TEMPERATURES) - 1)]
        try:
            return extract_batch(client, contents, categories_prompt, response_schema, temperature), None
        except Exception as e:
            error = e
            print(f"  Attempt {attempt}/{MAX_RETRIES} failed for pages {start_page}-{end_page} (temperature={temperature}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    return None, error


def check_completeness(document_pdf_path, statements, start_page=1, end_page=None):
    """Cross-checks CAPÍTULO/Artículo headings found in the source PDF
    (restricted to pages start_page-end_page) against the extracted
    statements, surfacing silently dropped chapters or short articles
    instead of leaving them to be found by hand."""
    with pdfplumber.open(document_pdf_path) as pdf:
        pages = pdf.pages[start_page - 1:end_page]
        full_text = "\n".join(page.extract_text() or "" for page in pages)

    raw_text_blob = " ".join(s.get("Raw Statement", "") for s in statements)
    section_marker_blob = " ".join(s.get("Section Marker", "") for s in statements)

    chapters = re.findall(r"CAP[IÍ]TULO\s+[IVXLC]+[^\n]*", full_text)
    missing_chapters = [c.strip() for c in chapters if c.strip()[:20] not in section_marker_blob]

    articles = sorted(set(int(n) for n in re.findall(r"Art[ií]culo\s+(\d+)", full_text)))
    missing_articles = [n for n in articles if f"Artículo {n}" not in raw_text_blob]

    if missing_chapters:
        print(f"WARNING: {len(missing_chapters)} chapter heading(s) never appear in any extracted Section Marker:")
        for c in missing_chapters:
            print(f"  - {c}")
    if missing_articles:
        print(f"WARNING: {len(missing_articles)} Artículo(s) never appear in any extracted Raw Statement: {missing_articles}")
    if not missing_chapters and not missing_articles:
        print("Completeness check passed: every chapter and Artículo in the document shows up in at least one extracted statement.")


def _normalize_for_matching(text):
    text = re.sub(r"\[[^\]]*\]", "", text)  # strip guideline-sanctioned bracket insertions
    return re.sub(r"\s+", " ", text).strip()


def _best_local_ratio(needle, haystack, pad=60):
    if not needle:
        return 1.0
    matcher = difflib.SequenceMatcher(None, haystack, needle, autojunk=False)
    match = matcher.find_longest_match(0, len(haystack), 0, len(needle))
    if match.size == 0:
        return 0.0
    start = max(0, match.a - pad)
    end = min(len(haystack), match.a + match.size + pad)
    window = haystack[start:end]
    return difflib.SequenceMatcher(None, window, needle, autojunk=False).ratio()


def check_groundedness(document_pdf_path, statements, start_page=1, end_page=None, threshold=0.45):
    """Best-effort check that each Raw Statement (outside [bracket]
    insertions) actually appears in the source PDF (restricted to pages
    start_page-end_page), to catch paraphrased or fabricated statements.
    Heuristic, not proof: pdfplumber mangles tables and hyphenation, so
    table-derived statements can legitimately score low — treat flags as
    worth a manual look, not definitive errors."""
    with pdfplumber.open(document_pdf_path) as pdf:
        pages = pdf.pages[start_page - 1:end_page]
        full_text = "\n".join(page.extract_text() or "" for page in pages)
    haystack = _normalize_for_matching(full_text)

    flagged = []
    for s in statements:
        raw = _normalize_for_matching(s.get("Raw Statement", ""))
        if not raw:
            continue
        ratio = _best_local_ratio(raw, haystack)
        if ratio < threshold:
            flagged.append((ratio, s.get("Statement No."), raw[:80]))

    if flagged:
        flagged.sort()
        print(f"WARNING: {len(flagged)} Raw Statement(s) scored below {threshold:.0%} similarity to the source PDF (possible paraphrase/fabrication — tables are a known false positive):")
        for ratio, no, snippet in flagged[:20]:
            print(f"  - [{no}] {ratio:.0%}: {snippet}...")
        if len(flagged) > 20:
            print(f"  ... and {len(flagged) - 20} more.")
    else:
        print(f"Groundedness check passed: every Raw Statement scored at or above {threshold:.0%} similarity to the source PDF.")


def parse_args():
    parser = argparse.ArgumentParser(
        description=f"Extract legal statements from a {PAGES_PER_CHUNK}-page chunk of the source document.",
    )
    parser.add_argument(
        "chunk",
        type=int,
        help=(
            f"1-based chunk index; chunk N processes pages "
            f"((N-1)*{PAGES_PER_CHUNK}+1)-(N*{PAGES_PER_CHUNK}) "
            f"(e.g. 1 = 1-{PAGES_PER_CHUNK}, 2 = {PAGES_PER_CHUNK + 1}-{PAGES_PER_CHUNK * 2}). "
            "Results are appended to the existing extraction_results.json."
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.chunk < 1:
        sys.exit("chunk must be a positive integer (1, 2, 3, ...).")

    client = genai.Client()

    document_pdf_path = DATA_DIR / "Document_for_processing.pdf"
    guideline_pdf_path = DATA_DIR / "guideline.pdf"
    aux_guideline_pdf_path = DATA_DIR / "inst-9-to-17.pdf"
    categories_path = DATA_DIR / "categories.csv"
    examples_path = DATA_DIR / "json_batches" / "all_examples.json"

    categories_prompt = build_categories_prompt(categories_path)
    base_prompt = build_base_prompt(examples_path)
    response_schema = build_response_schema(categories_path)

    print(f"Analyzing page count for {document_pdf_path}...")
    with pdfplumber.open(document_pdf_path) as pdf:
        total_pages = len(pdf.pages)

    run_start = (args.chunk - 1) * PAGES_PER_CHUNK + 1
    run_end = min(args.chunk * PAGES_PER_CHUNK, total_pages)
    if run_start > total_pages:
        max_chunk = -(-total_pages // PAGES_PER_CHUNK)  # ceil division
        sys.exit(f"Chunk {args.chunk} is out of range: the document has {total_pages} page(s), i.e. chunks 1-{max_chunk}.")
    print(f"Chunk {args.chunk}: processing pages {run_start}-{run_end} of {total_pages}.")

    print("Uploading PDFs to Gemini...")
    document = client.files.upload(file=document_pdf_path)
    guideline = client.files.upload(file=guideline_pdf_path)
    aux_guideline = client.files.upload(file=aux_guideline_pdf_path)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    output_filename = OUTPUT_DIR / "extraction_results.json"

    existing_text = output_filename.read_text(encoding="utf-8").strip() if output_filename.exists() else ""
    if existing_text:
        all_statements = json.loads(existing_text)
        print(f"Loaded {len(all_statements)} existing statement(s) from {output_filename}; new results will be appended.")
    else:
        all_statements = []

    new_statements = []
    failed_batches = []
    pending = deque((s, min(s + PAGES_PER_BATCH - 1, run_end)) for s in range(run_start, run_end + 1, PAGES_PER_BATCH))

    while pending:
        start_page, end_page = pending.popleft()
        print(f"Processing pages {start_page} to {end_page} of {total_pages}...")
        results, error = process_page_range(
            client, base_prompt, document, guideline, aux_guideline,
            categories_prompt, response_schema, start_page, end_page, total_pages,
        )

        if results is not None:
            renumber_batch(results, len(all_statements))
            all_statements.extend(results)
            new_statements.extend(results)
            save_progress(all_statements, output_filename)
        elif end_page - start_page + 1 > MIN_BATCH_PAGES:
            midpoint = (start_page + end_page) // 2
            print(f"  Splitting pages {start_page}-{end_page} into {start_page}-{midpoint} and {midpoint + 1}-{end_page} and retrying at a smaller granularity...")
            pending.appendleft((midpoint + 1, end_page))
            pending.appendleft((start_page, midpoint))
        else:
            failed_batches.append((start_page, end_page))
            debug_path = DEBUG_DIR / f"batch_{start_page:03d}_{end_page:03d}_error.txt"
            debug_path.write_text(str(error), encoding="utf-8")
            print(f"  Giving up on page {start_page} after {MAX_RETRIES} attempts at minimum granularity; continuing with the next batch.")

        time.sleep(2)

    save_progress(all_statements, output_filename)
    print(f"Chunk {args.chunk} complete. {len(new_statements)} new statement(s) added (total {len(all_statements)}) — saved to {output_filename}.")

    if failed_batches:
        pages = ", ".join(f"{s}-{e}" for s, e in failed_batches)
        print(f"WARNING: {len(failed_batches)} batch(es) failed after {MAX_RETRIES} attempts and were skipped: pages {pages}")
        print(f"See {DEBUG_DIR} for error details; re-run just those page ranges once the cause is fixed.")

    check_completeness(document_pdf_path, new_statements, run_start, run_end)
    check_groundedness(document_pdf_path, new_statements, run_start, run_end)
    check_bare_table_titles(new_statements)


if __name__ == "__main__":
    main()
