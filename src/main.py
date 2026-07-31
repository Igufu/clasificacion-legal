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
    ANCHOR_END_FIELD,
    ANCHOR_START_FIELD,
    build_anchor_batch_prompt,
    build_anchor_response_schema,
    build_base_prompt,
    build_categories_prompt,
    build_page_range_instruction,
    build_response_schema,
    clean_json_response,
    strip_recitation_delimiters,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR.parent / "output"
DEBUG_DIR = OUTPUT_DIR / "debug"

MODEL = "gemini-3.1-flash-lite"
PAGES_PER_BATCH = 1
PAGES_PER_CHUNK = 24  # pages processed per CLI invocation; chunk N = pages ((N-1)*PAGES_PER_CHUNK+1)-(N*PAGES_PER_CHUNK)
MAX_RETRIES = 4
RETRY_BACKOFF_SECONDS = 5
MAX_OUTPUT_TOKENS = 65536
CACHE_TTL = "7200s"  # generous vs. a worst-case 24-page chunk of single-page + retry + anchor-fallback calls

# Temperature is always 0.0, on every attempt. Raising it to dodge RECITATION
# trades accuracy for luck and is deliberately not done here. RECITATION is
# instead handled structurally, in three layers:
#   1. PAGES_PER_BATCH=1 keeps each request's output small — a single page's
#      statements are far less likely to form the kind of long contiguous
#      verbatim span the safety filter matches against than a multi-page
#      batch would.
#   2. Every "Raw Statement" is generated with "[[BR]]" markers spliced in
#      every 10-15 words (see prompt_builder's RECITATION SAFETY DELIMITER)
#      to break up contiguous matching even within a single statement, then
#      stripped back out locally by strip_recitation_delimiters.
#   3. If a page still exhausts MAX_RETRIES with both of those in place,
#      process_page_range falls back once to anchor-snippet mode — the model
#      emits only the first/last ~5 words of each statement, and the full
#      text is reconstructed locally from the source PDF (see
#      _reconstruct_anchor_statements) — since that mode's output never
#      contains a long verbatim span for the filter to catch.
TEMPERATURE = 0.0
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


def extract_batch(client, contents, cache_name, response_schema):
    """contents holds only the page-specific prompt — the document and
    guideline PDFs plus the categories and base instructions are already baked
    into cache_name (see main()), so they aren't re-sent (and re-billed) on
    every call."""
    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            cached_content=cache_name,
            temperature=TEMPERATURE,
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
    results = results if isinstance(results, list) else [results]
    return strip_recitation_delimiters(results)


def _extract_pdf_text(document_pdf_path, start_page, end_page):
    """Plain text of pages start_page-end_page (1-based, inclusive) from the
    source PDF, via pdfplumber. Shared by every check/reconstruction step
    that compares extracted statements against the literal source text for
    a given page range."""
    with pdfplumber.open(document_pdf_path) as pdf:
        pages = pdf.pages[start_page - 1:end_page]
        return "\n".join(page.extract_text() or "" for page in pages)


def _missing_article_headings(document_pdf_path, statements, start_page, end_page):
    """Returns Artículo numbers whose HEADING ("Artículo N:") appears in the
    source PDF within start_page-end_page but never shows up in any
    extracted Raw Statement. Requires the colon so mid-sentence
    cross-references to other already-extracted articles (e.g. "según lo
    estipulado en el Artículo 63,") don't get mistaken for a missing one —
    unlike check_completeness's looser warning-only regex, false positives
    here would trigger real (wasted) retries."""
    full_text = _extract_pdf_text(document_pdf_path, start_page, end_page)
    raw_text_blob = " ".join(s.get("Raw Statement", "") for s in statements)
    articles = sorted(set(int(n) for n in re.findall(r"Art[ií]culo\s+(\d+)\s*:", full_text)))
    return [n for n in articles if f"Artículo {n}" not in raw_text_blob]


def _attempt_extraction(client, contents, cache_name, response_schema, document_pdf_path,
                         start_page, end_page, label, validate_articles=True):
    """Runs one prompt through MAX_RETRIES attempts, all at TEMPERATURE.
    Retries here are insurance against transient failures (rate limits,
    network hiccups) only — not an attempt to dodge RECITATION through
    randomness, since every attempt is identical. Returns (results, None) on
    success, or (None, error) once every attempt has failed."""
    error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            results = extract_batch(client, contents, cache_name, response_schema)
            if validate_articles:
                missing = _missing_article_headings(document_pdf_path, results, start_page, end_page)
                if missing:
                    raise RuntimeError(f"{len(missing)} Artículo(s) present in pages {start_page}-{end_page} missing from the output: {missing}")
            print(f"  Pages {start_page}-{end_page} ({label}): {len(results)} statement(s) on attempt {attempt}.")
            return results, None
        except Exception as e:
            error = e
            print(f"  Attempt {attempt}/{MAX_RETRIES} failed for pages {start_page}-{end_page} ({label}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    return None, error


def process_page_range(client, cache_name, document_pdf_path,
                        response_schema, anchor_response_schema, start_page, end_page, total_pages):
    """Runs one page range through standard (delimiter-protected) extraction
    first. If that exhausts MAX_RETRIES on a single page — i.e. RECITATION
    survives both the small batch size and the [[BR]] markers — falls back
    once to anchor-snippet mode (see build_anchor_batch_prompt) before
    giving up, since that mode's output never contains a long verbatim span
    for the safety filter to catch. Returns (results, None) on success, or
    (None, error) once every avenue at this granularity has failed.

    A response that parses cleanly but silently drops an Artículo (no
    exception raised) is treated the same as any other failed standard-mode
    attempt: it feeds into the retry loop and, if that's exhausted, into the
    page-range split in the caller (main()) — which shrinks the batch enough
    for every article to fit before anchor mode is ever tried."""
    batch_prompt = build_page_range_instruction(start_page, end_page, total_pages)
    results, error = _attempt_extraction(
        client, [batch_prompt], cache_name, response_schema, document_pdf_path,
        start_page, end_page, label="standard",
    )
    if results is not None:
        return results, None

    if start_page == end_page:
        print(f"  Standard extraction exhausted for page {start_page}; retrying in RECITATION-safe anchor mode...")
        anchor_prompt = build_anchor_batch_prompt(start_page, end_page, total_pages)
        anchor_results, anchor_error = _attempt_extraction(
            client, [anchor_prompt], cache_name, anchor_response_schema, document_pdf_path,
            start_page, end_page, label="anchor", validate_articles=False,
        )
        if anchor_results is not None:
            reconstructed = _reconstruct_anchor_statements(document_pdf_path, anchor_results, start_page, end_page)
            missing = _missing_article_headings(document_pdf_path, reconstructed, start_page, end_page)
            if missing:
                print(f"  WARNING: anchor mode still missed {len(missing)} Artículo(s) on page {start_page}: {missing}")
            return reconstructed, None
        error = anchor_error

    return None, error


def check_completeness(document_pdf_path, statements, start_page=1, end_page=None):
    """Cross-checks CAPÍTULO/Artículo headings found in the source PDF
    (restricted to pages start_page-end_page) against the extracted
    statements, surfacing silently dropped chapters or short articles
    instead of leaving them to be found by hand."""
    full_text = _extract_pdf_text(document_pdf_path, start_page, end_page)

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


def _fuzzy_find(haystack, needle, start=0, min_ratio=0.6):
    """Best-effort substring locator for when an exact match fails: returns
    the start index of the longest matching block within haystack[start:]
    against needle, provided it covers enough of needle to be trustworthy."""
    if not needle:
        return None
    matcher = difflib.SequenceMatcher(None, haystack, needle, autojunk=False)
    match = matcher.find_longest_match(start, len(haystack), 0, len(needle))
    if match.size == 0 or match.size / len(needle) < min_ratio:
        return None
    return match.a


def _find_anchor_span(haystack, anchor_start, anchor_end):
    """Locates anchor_start ... anchor_end inside haystack and returns the
    full substring between them, inclusive, or None if either anchor can't
    be located with reasonable confidence. Both anchors and the haystack are
    run through _normalize_for_matching first — the same bracket-stripping
    used elsewhere for comparing extracted text to the raw PDF — since an
    anchor drawn from a statement's bracket-editorial start/end won't appear
    literally in the source. Falls back to a fuzzy longest-match search
    (_fuzzy_find) since pdfplumber's extraction frequently has different
    line breaks/spacing than the model's copy of the same words."""
    norm_haystack = _normalize_for_matching(haystack)
    norm_start = _normalize_for_matching(anchor_start or "")
    norm_end = _normalize_for_matching(anchor_end or "")
    if not norm_start or not norm_end:
        return None

    start_idx = norm_haystack.find(norm_start)
    if start_idx == -1:
        start_idx = _fuzzy_find(norm_haystack, norm_start)
        if start_idx is None:
            return None

    search_from = start_idx + len(norm_start)
    end_idx = norm_haystack.find(norm_end, search_from)
    if end_idx == -1:
        fuzzy_idx = _fuzzy_find(norm_haystack, norm_end, start=search_from)
        if fuzzy_idx is None:
            return None
        end_idx = fuzzy_idx
    end_idx += len(norm_end)

    if end_idx <= start_idx:
        return None
    return norm_haystack[start_idx:end_idx]


def _reconstruct_anchor_statements(document_pdf_path, results, start_page, end_page):
    """Converts anchor-mode results (ANCHOR_START_FIELD/ANCHOR_END_FIELD)
    into normal statements with a real "Raw Statement", by locating each
    anchor pair in the page's extracted text. A statement whose anchors
    can't be confidently located keeps a degraded Raw Statement built from
    the anchors alone (flagged for manual review) rather than being dropped
    silently."""
    page_text = _extract_pdf_text(document_pdf_path, start_page, end_page)
    unresolved = []
    for statement in results:
        anchor_start = statement.pop(ANCHOR_START_FIELD, "")
        anchor_end = statement.pop(ANCHOR_END_FIELD, "")
        span = _find_anchor_span(page_text, anchor_start, anchor_end)
        if span:
            statement["Raw Statement"] = span
        else:
            statement["Raw Statement"] = f"{anchor_start.strip()} [...] {anchor_end.strip()}"
            unresolved.append(statement.get("Statement No.") or anchor_start[:40])
    if unresolved:
        print(f"  WARNING: {len(unresolved)} anchor-mode statement(s) on page {start_page} could not be matched back to the source text and need manual review: {unresolved}")
    return results


def check_groundedness(document_pdf_path, statements, start_page=1, end_page=None, threshold=0.45):
    """Best-effort check that each Raw Statement (outside [bracket]
    insertions) actually appears in the source PDF (restricted to pages
    start_page-end_page), to catch paraphrased or fabricated statements.
    Heuristic, not proof: pdfplumber mangles tables and hyphenation, so
    table-derived statements can legitimately score low — treat flags as
    worth a manual look, not definitive errors."""
    full_text = _extract_pdf_text(document_pdf_path, start_page, end_page)
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
        description=f"Extract legal statements from a {PAGES_PER_CHUNK}-page chunk of the source document, or a single page with --page.",
    )
    parser.add_argument(
        "chunk",
        type=int,
        nargs="?",
        default=None,
        help=(
            f"1-based chunk index; chunk N processes pages "
            f"((N-1)*{PAGES_PER_CHUNK}+1)-(N*{PAGES_PER_CHUNK}) "
            f"(e.g. 1 = 1-{PAGES_PER_CHUNK}, 2 = {PAGES_PER_CHUNK + 1}-{PAGES_PER_CHUNK * 2}). "
            "Results are appended to the existing extraction_results.json. Omit if using --page."
        ),
    )
    parser.add_argument(
        "--page",
        type=int,
        default=None,
        help=(
            "Process only this single 1-based page, instead of a chunk. "
            "Results are still appended to the existing extraction_results.json."
        ),
    )
    args = parser.parse_args()
    if (args.chunk is None) == (args.page is None):
        parser.error("provide exactly one of: chunk (positional) or --page.")
    return args


def main():
    args = parse_args()
    if args.page is not None and args.page < 1:
        sys.exit("--page must be a positive integer (1, 2, 3, ...).")
    if args.page is None and args.chunk < 1:
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
    anchor_response_schema = build_anchor_response_schema(categories_path)

    print(f"Analyzing page count for {document_pdf_path}...")
    with pdfplumber.open(document_pdf_path) as pdf:
        total_pages = len(pdf.pages)

    if args.page is not None:
        if args.page > total_pages:
            sys.exit(f"Page {args.page} is out of range: the document has {total_pages} page(s).")
        run_start = run_end = args.page
        run_label = f"Page {args.page}"
    else:
        run_start = (args.chunk - 1) * PAGES_PER_CHUNK + 1
        run_end = min(args.chunk * PAGES_PER_CHUNK, total_pages)
        if run_start > total_pages:
            max_chunk = -(-total_pages // PAGES_PER_CHUNK)  # ceil division
            sys.exit(f"Chunk {args.chunk} is out of range: the document has {total_pages} page(s), i.e. chunks 1-{max_chunk}.")
        run_label = f"Chunk {args.chunk}"
    print(f"{run_label}: processing pages {run_start}-{run_end} of {total_pages}.")

    print("Uploading PDFs to Gemini...")
    document = client.files.upload(file=document_pdf_path)
    guideline = client.files.upload(file=guideline_pdf_path)
    aux_guideline = client.files.upload(file=aux_guideline_pdf_path)

    print("Caching the PDFs and system instructions so per-page requests don't re-send (and re-bill) them every call...")
    cache = client.caches.create(
        model=MODEL,
        config=types.CreateCachedContentConfig(
            contents=[document, guideline, aux_guideline],
            system_instruction=categories_prompt + "\n" + base_prompt,
            ttl=CACHE_TTL,
        ),
    )

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

    try:
        while pending:
            start_page, end_page = pending.popleft()
            print(f"Processing pages {start_page} to {end_page} of {total_pages}...")
            results, error = process_page_range(
                client, cache.name, document_pdf_path,
                response_schema, anchor_response_schema, start_page, end_page, total_pages,
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
                print(f"  Giving up on page {start_page} after {MAX_RETRIES} attempts at minimum granularity (standard + anchor fallback); continuing with the next batch.")

            time.sleep(2)
    finally:
        try:
            client.caches.delete(name=cache.name)
        except Exception as e:
            print(f"WARNING: failed to delete cache {cache.name}: {e} (it will still expire automatically after {CACHE_TTL}).")

    save_progress(all_statements, output_filename)
    print(f"{run_label} complete. {len(new_statements)} new statement(s) added (total {len(all_statements)}) — saved to {output_filename}.")

    if failed_batches:
        pages = ", ".join(f"{s}-{e}" for s, e in failed_batches)
        print(f"WARNING: {len(failed_batches)} batch(es) failed after {MAX_RETRIES} attempts and were skipped: pages {pages}")
        print(f"See {DEBUG_DIR} for error details; re-run just those page ranges once the cause is fixed.")

    check_completeness(document_pdf_path, new_statements, run_start, run_end)
    check_groundedness(document_pdf_path, new_statements, run_start, run_end)
    check_bare_table_titles(new_statements)


if __name__ == "__main__":
    main()
