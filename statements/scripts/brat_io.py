"""brat standoff read/write helpers shared by the v2 scripts.

T/R line regexes are reused from nlp-tagging/src/merge_literals.py. Two
things are added on top of that parser:

  - Lines are stripped of "\\r\\n", not just "\\n": the checked-out .ann files
    have CRLF endings (git core.autocrlf), and a trailing "\\r" would
    otherwise end up inside the annotation text.
  - Lines that are not T/R/E/A brat lines (e.g. the free-text notes at the
    end of standoff_comp.ann) are returned separately instead of being
    silently dropped, so callers can report them.

Also holds the document loader: document_extractor.get_document_text()
rewrites outputs/document.txt as a side effect, so v2 calls the pure
build_document_text(load_xml_bytes()) and checks it equals document.txt.
"""

import re

from paths import DOC_TXT_PATH
from document_extractor import build_document_text, load_xml_bytes
from merge_literals import RLINE_RE, TLINE_RE

ELINE_RE = re.compile(r"^E(\d+)\t(\w+):T(\d+)((?: \w+:[TE]\d+)*)$")
ALINE_RE = re.compile(r"^A(\d+)\t(\w+) ([TRE]\d+)(?: (.*))?$")


def load_document_text():
    doc_text = build_document_text(load_xml_bytes())
    with open(DOC_TXT_PATH, encoding="utf-8", newline="") as f:
        on_disk = f.read()
    if doc_text != on_disk:
        raise AssertionError(
            f"{DOC_TXT_PATH} differs from the text rebuilt from the raw XML; "
            "offsets in the existing .ann files may not line up."
        )
    return doc_text


def read_ann(path):
    """Parse a brat .ann file.

    Returns dict with:
      entities  -- [{"tid": int, "label", "start", "end", "text"}] in file order
      relations -- [{"rid": int, "label", "arg1": int, "arg2": int}]
      other     -- [(line_no, raw_line)] for every line that isn't T/R/E/A
    """
    entities, relations, events, attributes, other = [], [], [], [], []
    with open(path, encoding="utf-8", newline="") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.rstrip("\r\n")
            m = TLINE_RE.match(line)
            if m:
                entities.append(
                    {
                        "tid": int(m.group(1)),
                        "label": m.group(2),
                        "start": int(m.group(3)),
                        "end": int(m.group(4)),
                        "text": m.group(5),
                    }
                )
                continue
            m = re.match(r"^R(\d+)\t", line)
            m2 = RLINE_RE.match(line)
            if m and m2:
                relations.append(
                    {
                        "rid": int(m.group(1)),
                        "label": m2.group(1),
                        "arg1": int(m2.group(2)),
                        "arg2": int(m2.group(3)),
                    }
                )
                continue
            m = ELINE_RE.match(line)
            if m:
                events.append(
                    {
                        "eid": int(m.group(1)),
                        "label": m.group(2),
                        "trigger": int(m.group(3)),
                        "args": [tuple(a.split(":", 1)) for a in m.group(4).split()],
                    }
                )
                continue
            m = ALINE_RE.match(line)
            if m:
                attributes.append(
                    {
                        "aid": int(m.group(1)),
                        "label": m.group(2),
                        "target": m.group(3),
                        "value": m.group(4),
                    }
                )
                continue
            other.append((line_no, line))
    return {
        "entities": entities,
        "relations": relations,
        "events": events,
        "attributes": attributes,
        "other": other,
    }


def t_line(tid, label, start, end, text):
    return f"T{tid}\t{label} {start} {end}\t{text}"


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8", newline="") as f:
        for line in lines:
            f.write(line + "\n")


def write_doc_copy(doc_text, path):
    """brat needs a .txt with the same basename next to each .ann."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(doc_text)
