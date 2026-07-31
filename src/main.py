import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from dotenv import load_dotenv
import pdfplumber
from google import genai
from google.genai import types

from prompt_builder import (
    build_base_prompt,
    build_categories_prompt,
    build_document_batch_prompt,
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
PAGES_PER_CHUNK = 24  # pages processed per CLI invocation; chunk N = pages ((N-1)*PAGES_PER_CHUNK+1)-(N*PAGES_PER_CHUNK)
MAX_OUTPUT_TOKENS = 65536
CACHE_TTL = "7200s"
TEMPERATURE = 0.0

ARTICLE_HEADING_RE = re.compile(r"Art[ií]culo\s+(\d+)\s*:")
CAPITULO_RE = re.compile(r"CAP[IÍ]TULO\s+[IVXLC]+[^\n]*")

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
    """Single call, no retries — contents holds only the page-specific
    prompt (with the isolated document text embedded, see
    build_document_batch_prompt); the guideline PDFs plus the categories and
    base instructions are already baked into cache_name (see main())."""
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
    source PDF, via pdfplumber."""
    with pdfplumber.open(document_pdf_path) as pdf:
        pages = pdf.pages[start_page - 1:end_page]
        return "\n".join(page.extract_text() or "" for page in pages)


def _page_end_offsets(document_pdf_path):
    """Returns (full_text, end_offsets): full_text is the whole document's
    text, pages joined the same way _extract_pdf_text joins a sub-range
    ("\n".join(...)); end_offsets[p] is the character offset in full_text
    where page p's text ends (1-based page numbers, end_offsets[0] == 0).
    Used by _extend_to_article_boundary to compare Artículo heading
    positions against page boundaries."""
    with pdfplumber.open(document_pdf_path) as pdf:
        page_texts = [page.extract_text() or "" for page in pdf.pages]
    end_offsets = [0]
    for text in page_texts:
        end_offsets.append(end_offsets[-1] + len(text) + 1)  # +1 for the "\n" joiner
    return "\n".join(page_texts), end_offsets


def _extend_to_article_boundary(document_pdf_path, end_page, total_pages):
    """Grows end_page forward until the last Artículo heading that starts
    within [1, end_page] is actually closed — i.e. the next Artículo heading
    after it also falls within [1, end_page], proving the current one ended
    before end_page (or there is no next heading in the whole document, in
    which case the last Artículo simply runs to the end of the document).
    This is what keeps an Artículo from being cut off between two separate
    prompts: rather than trusting a page-count boundary chosen without
    regard to article structure, the boundary is moved to wherever the last
    Artículo in range actually ends — headings essentially never fall
    exactly at a page break, so checking page-start text (as a first,
    discarded version of this function did) missed almost every real case."""
    if end_page >= total_pages:
        return end_page
    full_text, end_offsets = _page_end_offsets(document_pdf_path)
    headings = [m.start() for m in ARTICLE_HEADING_RE.finditer(full_text)]

    boundary = end_offsets[end_page]
    included = [pos for pos in headings if pos < boundary]
    if not included:
        return end_page  # no Artículo heading in range at all; nothing to protect

    later = [pos for pos in headings if pos > included[-1]]
    if not later:
        return total_pages  # last Artículo in the document has no closing heading; it runs to EOF

    next_pos = later[0]
    while end_page < total_pages and end_offsets[end_page] <= next_pos:
        end_page += 1
    return end_page


def _most_recent_chapter_heading(document_pdf_path, start_page):
    """Scans pages 1..start_page-1 for the last CAPÍTULO heading, so the
    model can still prefix Section Markers with the right chapter even
    though it's no longer given the full document to look back through
    itself (see build_document_batch_prompt)."""
    if start_page <= 1:
        return None
    full_text = _extract_pdf_text(document_pdf_path, 1, start_page - 1)
    matches = CAPITULO_RE.findall(full_text)
    return matches[-1].strip() if matches else None


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


def _parse_page_range(value):
    match = re.fullmatch(r"(\d+)-(\d+)", value)
    if not match:
        raise argparse.ArgumentTypeError(f"invalid page range {value!r}; expected START-END (e.g. 18-24)")
    start, end = int(match.group(1)), int(match.group(2))
    if start < 1 or end < start:
        raise argparse.ArgumentTypeError(f"invalid page range {value!r}; START must be >=1 and END >= START")
    return start, end


def parse_args():
    parser = argparse.ArgumentParser(
        description=f"Extract legal statements from a {PAGES_PER_CHUNK}-page chunk of the source document, a single page with --page, or a page range with --pages.",
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
            "Results are appended to the existing extraction_results.json. Omit if using --page or --pages."
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
    parser.add_argument(
        "--pages",
        type=_parse_page_range,
        default=None,
        help=(
            "Process this inclusive 1-based page range, e.g. 18-24, instead of a chunk. "
            "Results are still appended to the existing extraction_results.json."
        ),
    )
    args = parser.parse_args()
    if sum(x is not None for x in (args.chunk, args.page, args.pages)) != 1:
        parser.error("provide exactly one of: chunk (positional), --page, or --pages.")
    return args


def main():
    args = parse_args()
    if args.page is not None and args.page < 1:
        sys.exit("--page must be a positive integer (1, 2, 3, ...).")
    if args.page is None and args.pages is None and args.chunk < 1:
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

    if args.page is not None:
        if args.page > total_pages:
            sys.exit(f"Page {args.page} is out of range: the document has {total_pages} page(s).")
        run_start, run_end = args.page, args.page
        run_label = f"Page {args.page}"
    elif args.pages is not None:
        run_start, run_end = args.pages
        if run_end > total_pages:
            sys.exit(f"Page range {run_start}-{run_end} is out of range: the document has {total_pages} page(s).")
        run_label = f"Pages {run_start}-{run_end}"
    else:
        run_start = (args.chunk - 1) * PAGES_PER_CHUNK + 1
        run_end = min(args.chunk * PAGES_PER_CHUNK, total_pages)
        if run_start > total_pages:
            max_chunk = -(-total_pages // PAGES_PER_CHUNK)  # ceil division
            sys.exit(f"Chunk {args.chunk} is out of range: the document has {total_pages} page(s), i.e. chunks 1-{max_chunk}.")
        run_label = f"Chunk {args.chunk}"

    extended_end = _extend_to_article_boundary(document_pdf_path, run_end, total_pages)
    if extended_end != run_end:
        print(f"Extending end page {run_end} to {extended_end} so the last Artículo in range isn't cut off.")
    run_end = extended_end
    print(f"{run_label}: processing pages {run_start}-{run_end} of {total_pages}.")

    document_text = _extract_pdf_text(document_pdf_path, run_start, run_end)
    chapter_context = _most_recent_chapter_heading(document_pdf_path, run_start)

    print("Uploading guideline PDFs to Gemini...")
    guideline = client.files.upload(file=guideline_pdf_path)
    aux_guideline = client.files.upload(file=aux_guideline_pdf_path)

    print("Caching the guideline PDFs and system instructions so they aren't re-sent (and re-billed) every call...")
    cache = client.caches.create(
        model=MODEL,
        config=types.CreateCachedContentConfig(
            contents=[guideline, aux_guideline],
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

    batch_prompt = build_document_batch_prompt(document_text, chapter_context, run_start, run_end, total_pages)

    new_statements = []
    try:
        new_statements = extract_batch(client, [batch_prompt], cache.name, response_schema)
        renumber_batch(new_statements, len(all_statements))
        all_statements.extend(new_statements)
        save_progress(all_statements, output_filename)
        print(f"{run_label} complete: {len(new_statements)} statement(s) extracted (total {len(all_statements)}) — saved to {output_filename}.")
    except Exception as e:
        debug_path = DEBUG_DIR / f"batch_{run_start:03d}_{run_end:03d}_error.txt"
        debug_path.write_text(str(e), encoding="utf-8")
        print(f"ERROR: extraction failed for pages {run_start}-{run_end}: {e}")
        print(f"See {debug_path} for details.")
    finally:
        try:
            client.caches.delete(name=cache.name)
        except Exception as e:
            print(f"WARNING: failed to delete cache {cache.name}: {e} (it will still expire automatically after {CACHE_TTL}).")

    check_groundedness(document_pdf_path, new_statements, run_start, run_end)
    check_bare_table_titles(new_statements)


if __name__ == "__main__":
    main()
