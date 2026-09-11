"""Locate the Deontic surface phrase inside each statement's span.

The Raw Statement column in PLAN_INSUMO.xlsx marks the surface phrase that
carries the deontic modality with **bold** formatting (see
`excel_to_json.py`, which stores it as `deontic_surface`). Sometimes that
phrase is the modal itself ("deberán", "podrán"), sometimes a future-tense
verb that stands in for an implied "[deberá]" ("generará", "iniciará"), and
sometimes a paraphrase ("prohíbe la operación", "será fiscalizada").

The Excel's "Deontic" column supplies the canonical modality for each row,
which is what the brat annotation *type* is derived from — the surface
phrase alone is ambiguous ("diseñará" isn't literally a modal, but the
row's canonical value tells us it stands in for "[deberá]"). Brackets in
the canonical value flag implicit modality and are stripped from the
token but retained as an "_implicit" suffix on the type.

Examples of the type produced:
    "deberán"        -> "Deontic_deberán"
    "[deberá]"       -> "Deontic_deberá_implicit"
    "solo podrán"    -> "Deontic_solo_podrán"
    "no [podrán]"    -> "Deontic_no_podrán_implicit"

Given a document.txt statement span already located by `tag_attribute.py`,
we search for the bold surface inside the span and emit one annotation per
hit, tagged with the derived type.
"""

from matching import (
    BRACKET_RE,
    find_exact,
    find_whitespace_insensitive,
    reject_multiline,
)

DEONTIC_TYPE_PREFIX = "Deontic"
FALLBACK_DEONTIC_TYPE = DEONTIC_TYPE_PREFIX


def canonicalize_deontic(value):
    """Convert an Excel "Deontic" cell value into (token, is_implicit).

    - Whitespace is stripped and internal runs collapsed.
    - `[` / `]` anywhere in the value marks the whole modality as implicit
      (row 24's "[no deben]" and row 28's "no [podrán]" both count).
    - Brackets are removed from the token; internal spaces become "_" so
      the token is safe to embed in a brat type name.

    Returns (None, False) if the value is blank/absent.
    """
    if value is None:
        return None, False
    text = str(value).strip()
    if not text:
        return None, False
    is_implicit = "[" in text or "]" in text
    cleaned = text.replace("[", "").replace("]", "")
    cleaned = " ".join(cleaned.split())
    if not cleaned:
        return None, is_implicit
    return cleaned.replace(" ", "_"), is_implicit


def deontic_type_for(value):
    """Return the brat type name for a given Excel Deontic value."""
    token, is_implicit = canonicalize_deontic(value)
    if token is None:
        return FALLBACK_DEONTIC_TYPE
    return f"{DEONTIC_TYPE_PREFIX}_{token}_implicit" if is_implicit else f"{DEONTIC_TYPE_PREFIX}_{token}"


def match_deontic(statement_text, deontic_surface):
    """Try to locate the bold `deontic_surface` inside `statement_text`.

    Returns (local_start, local_end, matched_text) or None. The strategy
    mirrors `tag_attribute.match_attribute`: exact match first, then a
    bracketed-fragment strip (belt-and-suspenders — bold runs shouldn't
    normally contain "[...]", but a stray bracket must not defeat the
    match), then whitespace-insensitive variants.
    """
    result = reject_multiline(find_exact(statement_text, deontic_surface))
    if result:
        return result

    stripped = BRACKET_RE.sub("", deontic_surface).strip()

    if stripped and stripped != deontic_surface:
        result = reject_multiline(find_exact(statement_text, stripped))
        if result:
            return result

    result = reject_multiline(
        find_whitespace_insensitive(statement_text, deontic_surface)
    )
    if result:
        return result

    if stripped and stripped != deontic_surface:
        result = reject_multiline(find_whitespace_insensitive(statement_text, stripped))
        if result:
            return result

    return None


def tag_deontic_for_span(doc_text, stmt, start, end):
    """Return a Deontic annotation for `stmt` inside doc_text[start:end], or None.

    `start`/`end` come from the statement-span resolution done upstream in
    `tag_attribute.tag_statements`, so we don't need to relocate the
    statement itself here.
    """
    surface = stmt.get("deontic_surface")
    if not surface:
        return None

    match = match_deontic(doc_text[start:end], surface)
    if match is None:
        return None

    local_start, local_end, matched_text = match
    deontic_value = stmt.get("deontic")
    return {
        "start": start + local_start,
        "end": start + local_end,
        "text": matched_text,
        "deontic": deontic_value,
        "type": deontic_type_for(deontic_value),
    }
