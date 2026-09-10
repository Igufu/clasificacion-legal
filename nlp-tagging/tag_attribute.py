"""Stage 2: tag Institutional Grammar "Attribute" spans as brat standoff annotations.

The raw document used for delimitation is the OFFICIAL full text of the norma,
fetched from LeyChile (https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma=...),
not a synthetic concatenation of the Excel's Raw Statement fragments.

Pipeline:
  1. Download (or reuse a cached) LeyChile XML export and extract its plain
     text -> document.txt (header, articles/chapters, promulgation clause,
     and any textual annexes; embedded binary attachments such as inline
     scanned images/tables are skipped).
  2. Load statements.json. For each statement, locate its raw_statement text
     inside document.txt (exact match, else whitespace-insensitive match) to
     get its real start/end offset. Statements that cannot be located are
     logged to unmatched_statements.csv.
  3. Within each located statement's span, locate its attribute text (exact
     match; else stripping bracketed "[implied]" segments; else
     whitespace-insensitive) and convert to a global offset. Attributes that
     cannot be located are logged to unmatched.csv.
  4. Write document.ann with one line per matched attribute.
"""

import bisect
import csv
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
JSON_PATH = BASE_DIR / "statements.json"
DOC_TXT_PATH = BASE_DIR / "document.txt"
DOC_ANN_PATH = BASE_DIR / "document.ann"
UNMATCHED_CSV_PATH = BASE_DIR / "unmatched.csv"
UNMATCHED_STATEMENTS_CSV_PATH = BASE_DIR / "unmatched_statements.csv"

NORMA_ID = 1111283
XML_URL = f"https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma={NORMA_ID}"
RAW_XML_PATH = BASE_DIR / "leychile_raw.xml"

LC_NS = "{http://www.leychile.cl/esquemas}"

BRACKET_RE = re.compile(r"\[[^\]]*\]")


# --------------------------------------------------------------------------
# Step 1: fetch the official document text from LeyChile
# --------------------------------------------------------------------------


def download_xml():
    req = urllib.request.Request(XML_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    RAW_XML_PATH.write_bytes(data)
    return data


def extract_mixed_text(texto_el):
    """Concatenate a <Texto> element's own text flow.

    LeyChile inlines embedded binary attachments (e.g. scanned charts) as
    child elements inside <Texto>. We skip each child's own subtree (which
    may hold base64 image data) but keep its `.tail`, i.e. the narrative
    text that follows it, so the surrounding prose stays intact.
    """
    parts = [texto_el.text or ""]
    for child in texto_el:
        parts.append(child.tail or "")
    return "".join(parts)


def collect_body_text(estructuras_funcionales_el, out):
    for el in estructuras_funcionales_el.findall(LC_NS + "EstructuraFuncional"):
        texto = el.find(LC_NS + "Texto")
        if texto is not None:
            out.append(extract_mixed_text(texto))
        children = el.find(LC_NS + "EstructurasFuncionales")
        if children is not None:
            collect_body_text(children, out)


def build_document_text(xml_bytes):
    root = ET.fromstring(xml_bytes)
    pieces = []

    encabezado = root.find(LC_NS + "Encabezado")
    if encabezado is not None:
        texto = encabezado.find(LC_NS + "Texto")
        if texto is not None:
            pieces.append(extract_mixed_text(texto))

    body = []
    ef_root = root.find(LC_NS + "EstructurasFuncionales")
    if ef_root is not None:
        collect_body_text(ef_root, body)
    pieces.extend(body)

    promulgacion = root.find(LC_NS + "Promulgacion")
    if promulgacion is not None:
        texto = promulgacion.find(LC_NS + "Texto")
        if texto is not None:
            pieces.append(extract_mixed_text(texto))

    anexos = root.find(LC_NS + "Anexos")
    if anexos is not None:
        for anexo in anexos.findall(LC_NS + "Anexo"):
            texto = anexo.find(LC_NS + "Texto")
            if texto is not None:
                pieces.append(extract_mixed_text(texto))

    return "".join(pieces)


def get_document_text():
    if RAW_XML_PATH.exists():
        xml_bytes = RAW_XML_PATH.read_bytes()
    else:
        xml_bytes = download_xml()

    doc_text = build_document_text(xml_bytes)

    with open(DOC_TXT_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(doc_text)

    return doc_text


# --------------------------------------------------------------------------
# Whitespace-insensitive matching helpers (shared by statement- and
# attribute-level lookups)
# --------------------------------------------------------------------------


def normalize_with_map(s):
    """Collapse runs of whitespace to a single space (and strip ends).

    Returns (normalized_string, index_map) where index_map[i] is the index
    in `s` that normalized_string[i] corresponds to.
    """
    chars = []
    index_map = []
    prev_was_space = True  # swallow leading whitespace
    for i, ch in enumerate(s):
        if ch.isspace():
            if not prev_was_space:
                chars.append(" ")
                index_map.append(i)
            prev_was_space = True
        else:
            chars.append(ch)
            index_map.append(i)
            prev_was_space = False

    while chars and chars[-1] == " ":
        chars.pop()
        index_map.pop()

    return "".join(chars), index_map


def clean(result):
    """Reject matches whose surface text embeds a raw newline.

    Such a span cannot be written as a single brat annotation line, so we
    treat it the same as "no match" and let the caller fall back further
    rather than guess.
    """
    if result is None:
        return None
    _, _, text = result
    if "\n" in text or "\r" in text:
        return None
    return result


# --------------------------------------------------------------------------
# Step 2: locate each statement's raw_statement inside the official document
# --------------------------------------------------------------------------


def find_statement_span(doc, doc_norm, doc_norm_map, raw_statement, search_from):
    idx = doc.find(raw_statement, search_from)
    if idx == -1:
        idx = doc.find(raw_statement)
    if idx != -1:
        return idx, idx + len(raw_statement)

    raw_norm, _ = normalize_with_map(raw_statement)
    if not raw_norm:
        return None

    norm_from = bisect.bisect_left(doc_norm_map, search_from)
    idx = doc_norm.find(raw_norm, norm_from)
    if idx == -1:
        idx = doc_norm.find(raw_norm)
    if idx == -1:
        return None

    start = doc_norm_map[idx]
    end = doc_norm_map[idx + len(raw_norm) - 1] + 1
    return start, end


# --------------------------------------------------------------------------
# Step 3: locate the attribute text inside its (now correctly offset)
# statement span
# --------------------------------------------------------------------------


def find_exact(text, candidate):
    idx = text.find(candidate)
    if idx == -1:
        return None
    return idx, idx + len(candidate), text[idx : idx + len(candidate)]


def find_whitespace_insensitive(text, candidate):
    candidate_norm, _ = normalize_with_map(candidate)
    if not candidate_norm:
        return None
    text_norm, text_map = normalize_with_map(text)
    idx = text_norm.find(candidate_norm)
    if idx == -1:
        return None
    start = text_map[idx]
    end = text_map[idx + len(candidate_norm) - 1] + 1
    return start, end, text[start:end]


def match_attribute(statement_text, attribute):
    """Try to locate `attribute` inside `statement_text`.

    Returns (local_start, local_end, matched_text) or None.
    """
    result = clean(find_exact(statement_text, attribute))
    if result:
        return result

    stripped = BRACKET_RE.sub("", attribute).strip()

    if stripped:
        result = clean(find_exact(statement_text, stripped))
        if result:
            return result

    result = clean(find_whitespace_insensitive(statement_text, attribute))
    if result:
        return result

    if stripped:
        result = clean(find_whitespace_insensitive(statement_text, stripped))
        if result:
            return result

    return None


def main():
    doc_text = get_document_text()
    doc_norm, doc_norm_map = normalize_with_map(doc_text)

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        statements = json.load(f)
    statements.sort(key=lambda s: s["stmt_no"])

    annotations = []
    unmatched_attributes = []
    unmatched_statements = []

    cursor = 0
    for stmt in statements:
        span = find_statement_span(doc_text, doc_norm, doc_norm_map, stmt["raw_statement"], cursor)
        if span is None:
            unmatched_statements.append(stmt)
            continue

        start, end = span
        cursor = end

        attribute = stmt["attribute"]
        if attribute is None:
            continue

        statement_text = doc_text[start:end]
        match = match_attribute(statement_text, attribute)
        if match is None:
            unmatched_attributes.append(stmt)
            continue

        local_start, local_end, matched_text = match
        annotations.append(
            {
                "start": start + local_start,
                "end": start + local_end,
                "text": matched_text,
            }
        )

    with open(DOC_ANN_PATH, "w", encoding="utf-8", newline="") as f:
        for i, ann in enumerate(annotations, start=1):
            f.write(f"T{i}\tAttribute {ann['start']} {ann['end']}\t{ann['text']}\n")

    with open(UNMATCHED_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["stmt_no", "attribute", "raw_statement"])
        for stmt in unmatched_attributes:
            writer.writerow([stmt["stmt_no"], stmt["attribute"], stmt["raw_statement"]])

    with open(UNMATCHED_STATEMENTS_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["stmt_no", "attribute", "raw_statement"])
        for stmt in unmatched_statements:
            writer.writerow([stmt["stmt_no"], stmt["attribute"], stmt["raw_statement"]])

    total = len(statements)
    with_attribute = sum(1 for s in statements if s["attribute"] is not None)
    located = total - len(unmatched_statements)
    tagged = len(annotations)

    print(f"Total statements: {total}")
    print(f"Statements located in official document: {located} (unmatched: {len(unmatched_statements)})")
    print(f"Statements with an attribute: {with_attribute}")
    print(f"Tagged: {tagged}")
    print(f"Unmatched attributes: {len(unmatched_attributes)}")


if __name__ == "__main__":
    main()
