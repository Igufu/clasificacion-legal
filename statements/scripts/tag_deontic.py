"""Locate the Deontic surface phrase inside each statement's span.

The Raw Statement column in PLAN_INSUMO.xlsx marks the surface phrase that
carries the deontic modality with **bold** formatting (see
`excel_to_json.py`, which stores it as `deontic_surface`). Sometimes that
phrase is the modal itself ("deberán", "podrán"), sometimes a future-tense
verb that stands in for an implied "[deberá]" ("generará", "iniciará"), and
sometimes a paraphrase ("prohíbe la operación", "será fiscalizada").

Every such phrase is tagged with the same brat type, "Deontic"; the
Excel's canonical "Deontic" column value (e.g. "deberán", "[podrá]") is
kept as the annotation's `deontic` field rather than folded into the type
name.

Given a document.txt statement span already located by `tag_attribute.py`,
we search for the bold surface inside the span and emit one annotation per
hit.
"""

from matching import (
    BRACKET_RE,
    find_exact,
    find_whitespace_insensitive,
    reject_multiline,
)

DEONTIC_TYPE = "Deontic"


def deontic_type_for(value):
    """Return the brat type name for a given Excel Deontic value.

    The brat *type* is always the plain "Deontic" label; the modal token
    itself (e.g. "deberán", "[podrán]") is recorded separately as the
    annotation's `deontic` field, not baked into the type name.
    """
    return DEONTIC_TYPE


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
