"""Whitespace-insensitive matching helpers.

Used both to locate a Raw Statement inside the official document and to
locate an Attribute inside its statement span.
"""

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
