"""Render triples.ann (T + binary R lines) as:

  - a top banner with the non-literal ratio for each role, so a reader
    knows up front what fraction of Excel values the Excel describes but
    the document doesn't carry verbatim;
  - one card per Excel row that produced at least one literal span: a
    small arc diagram with the row's Attribute / Deontic / DirectObject
    pseudo-tokens and one arc per binary relation present (AttrDeontic /
    AttrObject / DeonticObject), plus a detail row per span. Rows whose
    cells exist in Excel but didn't land literally in the text are listed
    separately with the reason;
  - the full document text from Capítulo III onward with every span
    highlighted inline, each with a chip pointing back to its statement.

Everything is one HTML page -- no mode toggle. There is only one version.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "statements" / "scripts"))

from paths import (  # noqa: E402
    LITERACY_JSON_PATH,
    TRIPLES_ANN_PATH,
    TRIPLES_JSONL_PATH,
    TRIPLES_TXT_PATH,
    TRIPLES_VIZ_HTML_PATH,
)

TLINE = re.compile(r"^(T\d+)\t(\S+) (\d+) (\d+)\t(.*)$")
RLINE = re.compile(r"^(R\d+)\t(\S+) Arg1:(T\d+) Arg2:(T\d+)$")

TYPE_COLORS = {
    "Deontic":      "#f6c177",
    "Attribute":    "#9ccfd8",
    "DirectObject": "#c4a7e7",
}
DEFAULT_COLOR = "#dcd7d2"
ROLE_LABELS = ("Attribute", "Deontic", "DirectObject")

RELATION_PAIR = {
    "AttrDeontic":   ("Attribute", "Deontic"),
    "AttrObject":    ("Attribute", "DirectObject"),
    "DeonticObject": ("Deontic", "DirectObject"),
}

CHAPTER_MARKER = "CAPÍTULO III"


def parse_ann(path):
    terms, relations = {}, []
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = TLINE.match(raw)
        if m:
            tid, ttype, start, end, text = m.groups()
            terms[tid] = {"id": tid, "type": ttype,
                          "start": int(start), "end": int(end),
                          "text": text}
            continue
        m = RLINE.match(raw)
        if m:
            rid, label, a1, a2 = m.groups()
            relations.append({"id": rid, "label": label, "arg1": a1, "arg2": a2})
    return terms, relations


def role_of(label):
    return label


def role_color(label):
    return TYPE_COLORS.get(label, DEFAULT_COLOR)


# --- Arc diagram -------------------------------------------------------------
# Hand-rolled SVG: one rounded box per role present on the row, variable
# width, "T# · Role" caption underneath, round cubic-bezier arcs for each
# binary relation.

_CHAR_W      = 7.2
_TAG_CHAR_W  = 6.4
_LINE_H      = 18
_TAG_LINE_H  = 14
_TAG_GAP     = 6
_BOX_PAD_X   = 12
_BOX_PAD_Y   = 7
_TOKEN_GAP   = 32
_ARC_BASE_H  = 36
_ARC_PER_HOP = 22
_MAX_CHARS   = 32


def _wrap(text, max_chars=_MAX_CHARS):
    tokens = " ".join(text.split()).split(" ")
    lines, cur, cur_len = [], [], 0
    for w in tokens:
        projected = cur_len + (1 if cur else 0) + len(w)
        if cur and projected > max_chars:
            lines.append(" ".join(cur))
            cur, cur_len = [w], len(w)
        else:
            cur.append(w)
            cur_len = projected
    if cur:
        lines.append(" ".join(cur))
    return lines or [""]


def render_row_arcs(spans, row_relations):
    """`spans` is [(label, tid, term)] in display order; `row_relations` is
    [(label, src_tid, dst_tid)]. Returns an SVG string, or "" if nothing to draw."""
    if not spans:
        return ""
    tokens, index_of = [], {}
    x = _BOX_PAD_X
    for i, (label, tid, term) in enumerate(spans):
        lines = _wrap(term["text"])
        tag = f"{tid} · {label}"
        text_w = max(len(ln) for ln in lines) * _CHAR_W
        tag_w = len(tag) * _TAG_CHAR_W
        box_w = max(text_w, tag_w) + 2 * _BOX_PAD_X
        tokens.append({"label": label, "tid": tid, "lines": lines, "tag": tag,
                       "left_x": x, "box_w": box_w, "center_x": x + box_w / 2})
        index_of[tid] = i
        x += box_w + _TOKEN_GAP
    total_w = x - _TOKEN_GAP + _BOX_PAD_X

    arcs = []
    for rel_label, src_tid, dst_tid in row_relations:
        if src_tid not in index_of or dst_tid not in index_of:
            continue
        lo = min(index_of[src_tid], index_of[dst_tid])
        hi = max(index_of[src_tid], index_of[dst_tid])
        hops = hi - lo
        arcs.append({"lo": lo, "hi": hi, "dest": index_of[dst_tid],
                     "label": rel_label, "h": _ARC_BASE_H + (hops - 1) * _ARC_PER_HOP})
    max_arc_h = max((a["h"] for a in arcs), default=0)

    arc_top_pad = 20
    box_top_y = arc_top_pad + max_arc_h + 6
    max_lines = max(len(tk["lines"]) for tk in tokens)
    box_h = max_lines * _LINE_H + 2 * _BOX_PAD_Y
    tag_y = box_top_y + box_h + _TAG_GAP + _TAG_LINE_H - 4
    svg_h = tag_y + 8

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {total_w:.0f} {svg_h:.0f}" '
        f'width="{total_w:.0f}" height="{svg_h:.0f}" '
        f'class="arc-svg" font-family="Inter, system-ui, sans-serif" '
        f'font-size="13">'
    ]

    arc_anchor_y = box_top_y
    for ai, arc in enumerate(arcs):
        x1 = tokens[arc["lo"]]["center_x"]
        x2 = tokens[arc["hi"]]["center_x"]
        y_top = arc_anchor_y - arc["h"]
        path_id = f'arc-{ai}'
        d = (f"M {x1:.1f},{arc_anchor_y:.1f} "
             f"C {x1:.1f},{y_top:.1f} {x2:.1f},{y_top:.1f} "
             f"{x2:.1f},{arc_anchor_y:.1f}")
        out.append(f'<path id="{path_id}" d="{d}" fill="none" '
                   f'stroke="#9a9a9a" stroke-width="1.4"/>')
        dest_x = tokens[arc["dest"]]["center_x"]
        out.append(f'<path d="M {dest_x:.1f},{arc_anchor_y:.1f} '
                   f'l -4,-7 l 8,0 z" fill="#9a9a9a"/>')
        out.append(
            f'<text font-size="11" fill="#555">'
            f'<textPath xlink:href="#{path_id}" startOffset="50%" '
            f'text-anchor="middle" side="left">'
            f'{html.escape(arc["label"])}</textPath></text>'
        )

    for tk in tokens:
        fill = role_color(tk["label"])
        out.append(
            f'<rect x="{tk["left_x"]:.1f}" y="{box_top_y:.1f}" '
            f'width="{tk["box_w"]:.1f}" height="{box_h:.1f}" '
            f'rx="6" ry="6" fill="{fill}" fill-opacity=".55" '
            f'stroke="rgba(0,0,0,.1)" stroke-width="1"/>'
        )
        text_block_h = len(tk["lines"]) * _LINE_H
        first_baseline = (box_top_y + (box_h - text_block_h) / 2 + _LINE_H - 5)
        out.append('<text text-anchor="middle" fill="#1b1b1b">')
        for li, line in enumerate(tk["lines"]):
            y = first_baseline + li * _LINE_H
            out.append(
                f'<tspan x="{tk["center_x"]:.1f}" y="{y:.1f}">'
                f'{html.escape(line)}</tspan>'
            )
        out.append('</text>')
        out.append(
            f'<text text-anchor="middle" font-size="11" '
            f'fill="#7a7a7a" font-family="ui-monospace, monospace" '
            f'x="{tk["center_x"]:.1f}" y="{tag_y:.1f}">'
            f'{html.escape(tk["tag"])}</text>'
        )
    out.append('</svg>')
    return f'<div class="arc-view">{"".join(out)}</div>'


# --- Row cards ---------------------------------------------------------------

ROLE_KEYS_IN_ORDER = (
    ("attribute", "Attribute"),
    ("deontic",   "Deontic"),
    ("object",    "DirectObject"),
)

TIER_LABEL = {
    "verbatim":    "verbatim",
    "fuzzy":       "fuzzy",
    "non_literal": "no match",
}


def _tier_badge(tier):
    label = TIER_LABEL.get(tier) or (tier or "")
    return f'<span class="tier-badge tier-{tier}">{html.escape(label)}</span>'


def render_row_card(row, terms):
    stmt_no = row["statement_no"]
    anchor = f"stmt-{stmt_no}"

    spans = []
    for key, label in ROLE_KEYS_IN_ORDER:
        tid = row[f"{key}_tid"]
        if tid is None:
            continue
        term = terms.get(tid)
        if term is None:
            continue
        spans.append((label, tid, term))

    row_relations = [(rel["label"], rel["arg1"], rel["arg2"])
                     for rel in row.get("relations", [])]
    arcs = render_row_arcs(spans, row_relations)

    rows_html = []
    for key, label in ROLE_KEYS_IN_ORDER:
        excel = row[f"{key}_excel"]
        literal = row[f"{key}_literal"]
        tid = row[f"{key}_tid"]
        text = row[f"{key}_text"]
        reason = row[f"{key}_reason"]
        tier = row[f"{key}_tier"]
        if excel is None and tid is None:
            # Empty Excel cell AND no span. Skip the row entirely.
            continue

        meta_parts = [_tier_badge(tier)]
        if literal and tid:
            meta_parts.append(
                f'<span class="offs">{tid} '
                f'[{row[f"{key}_span"][0]}&ndash;{row[f"{key}_span"][1]}]</span>'
            )
        meta = " ".join(meta_parts)

        if literal and tid:
            body_lines = [f'<div class="row-text">{html.escape(text)}</div>']
            if tier == "fuzzy":
                # Show the Excel version alongside so a reviewer can see what
                # was folded (case, accents, both).
                body_lines.append(
                    f'<div class="row-excel"><span class="row-excel-tag">Excel</span>'
                    f'{html.escape(excel or "")}</div>'
                )
            body = "".join(body_lines)
        else:
            tag = f' <span class="muted small">({html.escape(reason)})</span>' if reason else ""
            body = (f'<div class="row-text non-literal">'
                    f'<span class="row-excel-tag">Excel</span>'
                    f'{html.escape(excel or "")}{tag}</div>')

        rows_html.append(
            f'<div class="row" data-role="{key}">'
            f'<div class="role-chip" style="background:{role_color(label)}">{label}</div>'
            f'<div class="row-body"><div class="row-meta">{meta}</div>{body}</div>'
            '</div>'
        )

    rel_badges = ""
    if row_relations:
        rel_badges = " ".join(
            f'<span class="rel-badge">{html.escape(label)}</span>'
            for label, _, _ in row_relations
        )

    status = row["status"]
    status_chip = f'<span class="status-chip status-{status}">{status}</span>'
    header = (
        f'<h3 id="{anchor}">'
        f'<a class="anchor" href="#{anchor}">St. {stmt_no}</a> '
        f'{status_chip}'
        f'{rel_badges}'
        f'</h3>'
    )

    # data-roles-present / data-roles-literal drive the role filter so a card
    # can be hidden when none of its visible roles are selected.
    roles_present = ",".join(
        key for key, _ in ROLE_KEYS_IN_ORDER
        if (row[f"{key}_excel"] is not None) or row[f"{key}_tid"]
    )
    roles_literal = ",".join(
        key for key, _ in ROLE_KEYS_IN_ORDER if row[f"{key}_tid"]
    )
    return (f'<section class="row-card" data-roles-present="{roles_present}" '
            f'data-roles-literal="{roles_literal}">{header}{arcs}'
            f'<div class="row-grid">{"".join(rows_html)}</div></section>')


# --- Annotated full text -----------------------------------------------------

def slice_from_chapter_iii(text):
    idx = text.find(CHAPTER_MARKER)
    if idx < 0:
        return text, 0
    return text[idx:], idx


def render_annotated_text(text, terms, offset, tid_to_stmt, tid_to_tier):
    """Overlay every span onto the raw text, nesting with the split-and-reopen
    technique so overlapping spans produce valid HTML. Each inline span
    carries its role (so the role filter can hide it) and its match tier
    (verbatim = solid underline; fuzzy = dashed underline + ~ marker)."""
    unique = {}
    for t in terms.values():
        if t["start"] < offset or t["end"] > offset + len(text):
            continue
        key = (t["type"], t["start"], t["end"])
        unique.setdefault(key, {"type": t["type"], "start": t["start"],
                                "end": t["end"], "tids": []})["tids"].append(t["id"])
    spans = list(unique.values())

    boundaries = []
    for s in spans:
        boundaries.append((s["start"] - offset, 1, s))
        boundaries.append((s["end"] - offset, 0, s))
    boundaries.sort(key=lambda e: (
        e[0], e[1],
        -(e[2]["end"] - e[2]["start"]) if e[1] == 1
        else (e[2]["end"] - e[2]["start"]),
    ))

    def _stmt_label(s):
        stmt_nos = sorted({tid_to_stmt.get(tid) for tid in s["tids"] if tid in tid_to_stmt})
        stmt_nos = [n for n in stmt_nos if n is not None]
        return "St. " + ",".join(str(n) for n in stmt_nos) if stmt_nos else ""

    label_to_role = {"Attribute": "attribute", "Deontic": "deontic",
                     "DirectObject": "object"}

    def _span_tier(s):
        """verbatim beats fuzzy if a single physical span was tagged twice."""
        tiers = {tid_to_tier.get(tid) for tid in s["tids"]}
        tiers.discard(None)
        if "verbatim" in tiers:
            return "verbatim"
        if "fuzzy" in tiers:
            return "fuzzy"
        return "unknown"

    def open_tag(s):
        tids = ",".join(s["tids"])
        tier = _span_tier(s)
        title = f'{tids} · {s["type"]} · {tier} · {_stmt_label(s)}'
        role_key = label_to_role.get(s["type"], "")
        return (f'<span class="ann ann-{role_key} ann-tier-{tier}" '
                f'style="background:{role_color(s["type"])}"'
                f' title="{html.escape(title)}">')

    def close_tag(s, final):
        if not final:
            return "</span>"
        chip = _stmt_label(s)
        marker = '<sup class="fuzzy-marker" title="fuzzy match (case/accent-folded)">~</sup>' \
            if _span_tier(s) == "fuzzy" else ""
        chip_html = f'<sup class="eid">{html.escape(chip)}</sup>' if chip else ""
        return f'{marker}{chip_html}</span>'

    out, stack, pos = [], [], 0
    for ev_pos, kind, span in boundaries:
        if ev_pos > pos:
            out.append(html.escape(text[pos:ev_pos]))
            pos = ev_pos
        if kind == 1:
            out.append(open_tag(span))
            stack.append(span)
        else:
            if span not in stack:
                continue
            above = []
            while stack and stack[-1] is not span:
                inner = stack.pop()
                above.append(inner)
                out.append(close_tag(inner, final=False))
            stack.pop()
            out.append(close_tag(span, final=True))
            for inner in reversed(above):
                out.append(open_tag(inner))
                stack.append(inner)
    if pos < len(text):
        out.append(html.escape(text[pos:]))
    return "".join(out)


# --- Page shell --------------------------------------------------------------

HTML_SHELL = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>Triples visualization — DTO-31_24</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family: Inter, system-ui, sans-serif; margin: 2rem auto;
          max-width: 1100px; color: #1b1b1b; line-height: 1.5; }}
  h1 {{ margin: 0 0 .25rem; }}
  h2 {{ margin: 2rem 0 .5rem; font-size: 18px; }}
  h3 {{ margin: 0; font-size: 14px; }}
  .muted {{ color: #777; font-weight: normal; }}
  .small {{ font-size: 12px; }}

  .legend {{ margin: .5rem 0 1.5rem; display: flex; gap: 8px;
             flex-wrap: wrap; align-items: center; }}
  .chip {{ display: inline-block; padding: 2px 10px; border-radius: 10px;
           font-size: 12px; }}

  .literacy {{ display: grid; grid-template-columns: repeat(3, 1fr);
               gap: .75rem; margin: .5rem 0 1rem; }}
  .lit-card {{ border: 1px solid #ececec; border-radius: 8px;
               padding: .6rem .85rem; background: #fff; }}
  .lit-card .lit-head {{ display: flex; align-items: baseline; gap: .5rem;
                         justify-content: space-between; }}
  .lit-card .lit-ratio {{ font-size: 22px; font-weight: 600; }}
  .lit-card .lit-sub {{ color: #777; font-size: 12px; }}
  .lit-bar {{ display: flex; height: 8px; margin-top: .35rem;
              background: #eee; border-radius: 4px; overflow: hidden; }}
  .lit-bar > span {{ display: block; height: 100%; }}
  .lit-bar .seg-verbatim    {{ background: #7fb286; }}
  .lit-bar .seg-fuzzy       {{ background: #e2c477; }}
  .lit-bar .seg-non_literal {{ background: #d08b8b; }}
  .lit-breakdown {{ color: #666; font-size: 12px; margin-top: .25rem;
                     display: flex; gap: .5rem; flex-wrap: wrap; }}
  .lit-breakdown .seg {{ display: inline-flex; align-items: center;
                          gap: 4px; }}
  .lit-breakdown .dot {{ width: 8px; height: 8px; border-radius: 50%;
                          display: inline-block; }}

  /* --- Row cards --- */
  .row-card {{ border: 1px solid #ececec; border-radius: 8px;
               padding: .75rem 1rem; margin: .75rem 0; background: #fff; }}
  .row-card h3 {{ display: flex; gap: 6px; align-items: baseline;
                   flex-wrap: wrap; }}
  .row-card h3 .anchor {{ color: #555; text-decoration: none;
                           font-family: ui-monospace, monospace;
                           font-size: 12px; }}
  .status-chip {{ font-family: ui-monospace, monospace; font-size: 11px;
                   padding: 2px 8px; border-radius: 10px;
                   background: #eee; color: #333; }}
  .status-complete {{ background: #d7eadc; color: #1e4a2d; }}
  .status-pair     {{ background: #e4e4f2; color: #333; }}
  .status-single   {{ background: #f4e4d8; color: #624020; }}
  .status-no_literal_span {{ background: #f4d8d8; color: #7a2626; }}
  .status-all_cells_empty {{ background: #f0f0f0; color: #666; }}
  .rel-badge {{ font-family: ui-monospace, monospace; font-size: 11px;
                 padding: 2px 8px; border-radius: 10px;
                 background: #efefef; color: #333; border: 1px solid #e0e0e0; }}

  .row-grid .row {{ display: grid; grid-template-columns: 120px 1fr;
                     gap: .5rem 1rem; margin-top: .5rem; align-items: start; }}
  .role-chip {{ font-size: 11px; text-align: center;
                padding: 3px 8px; border-radius: 6px;
                font-weight: 600; color: #1b1b1b; }}
  .row-body {{ min-width: 0; }}
  .row-meta {{ color: #666; font-size: 12px;
               font-family: ui-monospace, monospace;
               display: flex; gap: 6px; align-items: center;
               flex-wrap: wrap; }}
  .row-meta .offs {{ color: #999; }}
  .row-text {{ font-size: 14px; word-wrap: break-word; }}
  .row-text.non-literal {{ color: #666; font-style: italic; }}
  .row-excel {{ font-size: 13px; color: #555; margin-top: 2px;
                font-style: italic; }}
  .row-excel-tag {{ font-family: ui-monospace, monospace; font-size: 10px;
                     color: #777; background: #f0f0f0;
                     padding: 1px 5px; border-radius: 3px;
                     margin-right: 6px; font-style: normal;
                     vertical-align: 1px; }}

  .tier-badge {{ font-family: ui-monospace, monospace; font-size: 10px;
                  padding: 2px 6px; border-radius: 10px;
                  border: 1px solid transparent; }}
  .tier-verbatim    {{ background: #dceadc; color: #1e4a2d;
                        border-color: #b8d6ba; }}
  .tier-fuzzy       {{ background: #f6ecc8; color: #6a4b14;
                        border-color: #e2d59a; }}
  .tier-non_literal {{ background: #f3d2d2; color: #7a2626;
                        border-color: #e4b2b2; }}

  .arc-view {{ margin: .5rem 0 .75rem; overflow-x: auto;
               padding-bottom: 4px; }}
  .arc-view svg.arc-svg {{ display: block; }}

  /* --- Annotated-text view --- */
  .passage {{ line-height: 2.3; font-size: 15px; white-space: pre-wrap; }}
  .passage .ann {{ padding: 1px 3px; border-radius: 3px;
                    box-shadow: inset 0 -2px 0 rgba(0,0,0,.08);
                    cursor: help; }}
  .passage .ann .ann {{ box-shadow: inset 0 -4px 0 rgba(0,0,0,.08); }}
  .passage .ann sup.eid {{ font-family: ui-monospace, monospace;
                            font-size: 9px; margin-left: 2px;
                            color: #333; opacity: .75;
                            background: rgba(255,255,255,.55);
                            padding: 0 2px; border-radius: 2px;
                            vertical-align: super; }}
  .passage .ann.hidden-role,
  .passage .ann.hidden-tier {{ background: transparent !important;
                                box-shadow: none; cursor: text; }}
  .passage .ann.hidden-role sup, .passage .ann.hidden-tier sup {{ display: none; }}
  /* Verbatim: solid underline (default inherited look). */
  .passage .ann-tier-verbatim {{ box-shadow: inset 0 -2px 0 rgba(30, 80, 30, .55); }}
  .passage .ann .ann-tier-verbatim {{ box-shadow: inset 0 -4px 0 rgba(30, 80, 30, .55); }}
  /* Fuzzy: dashed underline + small ~ marker so a reviewer can skim for them. */
  .passage .ann-tier-fuzzy {{
    box-shadow: inset 0 -2px 0 rgba(140, 100, 20, .9);
    background-image: linear-gradient(90deg,
        rgba(140,100,20,.9) 50%, transparent 50%);
    background-repeat: repeat-x;
    background-size: 6px 2px;
    background-position: 0 100%;
  }}
  .passage .fuzzy-marker {{ font-family: ui-monospace, monospace;
                             font-size: 10px; color: #8a5a10;
                             background: rgba(255,255,255,.7);
                             padding: 0 2px; margin-left: 2px;
                             border-radius: 2px; border: 1px solid rgba(140,100,20,.4);
                             vertical-align: super; }}

  .filter-bar {{ margin: .5rem 0 1rem; display: flex; gap: .75rem 1rem;
                  flex-wrap: wrap; align-items: center;
                  padding: .5rem .75rem; border: 1px solid #ececec;
                  border-radius: 8px; background: #fafafa; }}
  .filter-bar label {{ font-size: 13px; display: inline-flex;
                        align-items: center; gap: 4px; }}
  .filter-bar .filter-group {{ display: inline-flex; gap: .75rem;
                                 align-items: center; }}
  .filter-bar .sep {{ color: #ccc; }}
</style></head><body>
<h1>Triples — DTO-31_24</h1>
<p class="muted">Each Excel row looked up literally in its statement's text.
Binary relations (AttrDeontic / AttrObject / DeonticObject) connect every
pair of literal spans on the same row — no deontic trigger required.</p>

<h2>Match tiers per role</h2>
<p class="muted small">verbatim = span text matches the Excel cell up to whitespace.
fuzzy = required case / Spanish-accent folding (e.g. <code>amoniaco → amoníaco</code>).
no match = bracketed/implicit cell, or value not present in the statement at all.</p>
<div class="literacy">{literacy_cards}</div>

<div class="legend">{legend}</div>

<h2>Row cards <span class="muted">({n_rows_shown} of {n_rows_total} rows)</span></h2>
<div class="filter-bar">
  <strong>Roles:</strong>
  <div class="filter-group">
    <label><input type="checkbox" class="role-toggle" data-role="attribute" checked>
      Attribute</label>
    <label><input type="checkbox" class="role-toggle" data-role="deontic" checked>
      Deontic</label>
    <label><input type="checkbox" class="role-toggle" data-role="object" checked>
      DirectObject</label>
  </div>
  <span class="sep">|</span>
  <strong>Tiers:</strong>
  <div class="filter-group">
    <label><input type="checkbox" class="tier-toggle" data-tier="verbatim" checked>
      verbatim</label>
    <label><input type="checkbox" class="tier-toggle" data-tier="fuzzy" checked>
      fuzzy</label>
    <label><input type="checkbox" class="tier-toggle" data-tier="non_literal" checked>
      no match</label>
  </div>
  <span class="sep">|</span>
  <label><input type="checkbox" id="hide-empty" checked>
    hide cards with 0 visible spans</label>
</div>
<div id="rows">{cards}</div>

<h2>Full text with inline spans</h2>
<p class="muted">From {chapter_marker} onwards; the earlier chapters are prelude and carry no tags.</p>
<div class="passage">{passage}</div>

<script>
(function () {{
  var ROLES = ["attribute", "deontic", "object"];
  var TIERS = ["verbatim", "fuzzy", "non_literal"];
  var roleBoxes = {{}}, tierBoxes = {{}};
  ROLES.forEach(function (r) {{
    roleBoxes[r] = document.querySelector('input.role-toggle[data-role="' + r + '"]');
  }});
  TIERS.forEach(function (t) {{
    tierBoxes[t] = document.querySelector('input.tier-toggle[data-tier="' + t + '"]');
  }});
  var hideEmpty = document.getElementById("hide-empty");

  function apply() {{
    var roleOn = {{}}, tierOn = {{}};
    ROLES.forEach(function (r) {{ roleOn[r] = roleBoxes[r].checked; }});
    TIERS.forEach(function (t) {{ tierOn[t] = tierBoxes[t].checked; }});

    // Hide role-specific inline annotations in the passage.
    ROLES.forEach(function (r) {{
      document.querySelectorAll('.passage .ann-' + r).forEach(function (el) {{
        el.classList.toggle('hidden-role', !roleOn[r]);
      }});
    }});

    // Tier filter applies to the passage too (verbatim / fuzzy). The
    // "no match" tier is only ever a row-card state (no inline span to
    // hide), so it's skipped here.
    ["verbatim", "fuzzy"].forEach(function (t) {{
      document.querySelectorAll('.passage .ann-tier-' + t).forEach(function (el) {{
        el.classList.toggle('hidden-tier', !tierOn[t]);
      }});
    }});

    document.querySelectorAll('.row-card').forEach(function (card) {{
      var visibleSpans = 0;
      card.querySelectorAll('.row-grid > .row').forEach(function (row) {{
        var role = row.getAttribute('data-role');
        var tier = (row.querySelector('.tier-badge') || {{}}).className || '';
        var tierClass = (tier.match(/tier-(verbatim|fuzzy|non_literal)/) || [,""])[1];
        var show = roleOn[role] && (!tierClass || tierOn[tierClass]);
        row.style.display = show ? "" : "none";
        if (show) visibleSpans++;
      }});
      card.style.display = (hideEmpty.checked && visibleSpans === 0) ? "none" : "";
    }});
  }}

  Object.values(roleBoxes).concat(Object.values(tierBoxes))
    .concat([hideEmpty])
    .forEach(function (b) {{ b.addEventListener("change", apply); }});
  apply();
}})();
</script>
</body></html>
"""


def _literacy_card(role_info):
    label = role_info["label"]
    with_val = role_info["with_value"]
    verb_pct = int(round(role_info["verbatim_ratio"]    * 100))
    fuzz_pct = int(round(role_info["fuzzy_ratio"]       * 100))
    nolit_pct = max(0, 100 - verb_pct - fuzz_pct) if with_val else 0
    head_ratio = (f"{role_info['non_literal_ratio']:.1%} no match"
                  if with_val else "n/a")
    return (
        f'<div class="lit-card">'
        f'<div class="lit-head">'
        f'<span class="chip" style="background:{role_color(label)}">{label}</span>'
        f'<span class="lit-ratio">{head_ratio}</span>'
        f'</div>'
        f'<div class="lit-sub">'
        f'{role_info["verbatim"]} verbatim · {role_info["fuzzy"]} fuzzy · '
        f'{role_info["non_literal"]} no match '
        f'(de {with_val} celdas con valor; {role_info["empty"]} vacías)'
        f'</div>'
        f'<span class="lit-bar">'
        f'<span class="seg-verbatim"    style="width:{verb_pct}%"></span>'
        f'<span class="seg-fuzzy"       style="width:{fuzz_pct}%"></span>'
        f'<span class="seg-non_literal" style="width:{nolit_pct}%"></span>'
        f'</span>'
        f'<div class="lit-breakdown">'
        f'<span class="seg"><span class="dot" style="background:#7fb286"></span>verbatim</span>'
        f'<span class="seg"><span class="dot" style="background:#e2c477"></span>fuzzy</span>'
        f'<span class="seg"><span class="dot" style="background:#d08b8b"></span>no match</span>'
        f'</div>'
        f'</div>'
    )


def main():
    terms, _ = parse_ann(TRIPLES_ANN_PATH)
    with open(TRIPLES_JSONL_PATH, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]
    with open(LITERACY_JSON_PATH, encoding="utf-8") as f:
        literacy = json.load(f)

    tid_to_stmt, tid_to_tier = {}, {}
    for row in rows:
        for key, tier_key in (
            ("attribute_tid", "attribute_tier"),
            ("deontic_tid",   "deontic_tier"),
            ("object_tid",    "object_tier"),
        ):
            if row[key]:
                tid_to_stmt[row[key]] = row["statement_no"]
                tid_to_tier[row[key]] = row[tier_key]

    raw_text = TRIPLES_TXT_PATH.read_text(encoding="utf-8")
    text, offset = slice_from_chapter_iii(raw_text)

    rows_visible = [r for r in rows if r["status"] != "all_cells_empty"]
    cards = "".join(render_row_card(r, terms) for r in rows_visible)
    passage = render_annotated_text(text, terms, offset, tid_to_stmt, tid_to_tier)

    legend = " ".join(
        f'<span class="chip" style="background:{c}">{label}</span>'
        for label, c in TYPE_COLORS.items()
    )
    literacy_cards = "".join(
        _literacy_card(literacy["roles"][role])
        for role in ("attribute", "deontic", "object")
    )

    TRIPLES_VIZ_HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRIPLES_VIZ_HTML_PATH.write_text(
        HTML_SHELL.format(
            literacy_cards=literacy_cards,
            legend=legend,
            cards=cards,
            passage=passage,
            n_rows_shown=len(rows_visible),
            n_rows_total=len(rows),
            chapter_marker=CHAPTER_MARKER,
        ),
        encoding="utf-8",
    )
    print(f"-> {TRIPLES_VIZ_HTML_PATH}")


if __name__ == "__main__":
    main()
