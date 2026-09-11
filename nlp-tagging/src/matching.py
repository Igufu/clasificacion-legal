"""Whitespace-insensitive matching helpers.

Used both to locate a Raw Statement inside the official document and to
locate an Attribute inside its statement span.
"""

import bisect
import re

BRACKET_RE = re.compile(r"\[[^\]]*\]")


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


def reject_multiline(result):
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


def find_exact(text, candidate):
    idx = text.find(candidate)
    if idx == -1:
        return None
    return idx, idx + len(candidate), text[idx : idx + len(candidate)]


def find_whitespace_insensitive(text, candidate, ignore_case=False):
    candidate_norm, _ = normalize_with_map(candidate)
    if not candidate_norm:
        return None
    text_norm, text_map = normalize_with_map(text)
    haystack = text_norm.lower() if ignore_case else text_norm
    needle = candidate_norm.lower() if ignore_case else candidate_norm
    idx = haystack.find(needle)
    if idx == -1:
        return None
    start = text_map[idx]
    end = text_map[idx + len(needle) - 1] + 1
    return start, end, text[start:end]


def find_last_occurrence_before(doc_text, doc_norm, doc_norm_map, candidate, before_index, ignore_case=True):
    """Find the nearest occurrence of `candidate` in `doc_norm` ending at or
    before `before_index` (an offset into the original `doc_text`).

    Used to resolve an Attribute a coder bracketed because it isn't literally
    present in the current statement's own text -- the actor/object was
    typically already named explicitly in an earlier sentence of the same
    Article, so this searches backward through the whole document instead of
    just the statement's span. A candidate match embedding a raw newline is
    skipped (not a valid single-line brat span) and the search retries
    further back rather than accepting it.
    """
    candidate_norm, _ = normalize_with_map(candidate)
    if not candidate_norm:
        return None

    haystack = doc_norm.lower() if ignore_case else doc_norm
    needle = candidate_norm.lower() if ignore_case else candidate_norm

    search_end = bisect.bisect_left(doc_norm_map, before_index)
    while True:
        idx = haystack.rfind(needle, 0, search_end)
        if idx == -1:
            return None
        start = doc_norm_map[idx]
        end = doc_norm_map[idx + len(needle) - 1] + 1
        text = doc_text[start:end]
        if "\n" not in text and "\r" not in text:
            return start, end, text
        search_end = idx
