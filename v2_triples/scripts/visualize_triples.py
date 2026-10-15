"""Render triples.ann as per-event arc diagrams + detail rows + inline text.

Each event is shown as a displacy manual-dep arc diagram at the top of its
card, with the full text in rows underneath. The arc view uses short labels
(T#) so arcs never collide with their pseudo-tokens; the full literal text
lives below in detail rows (where line wrapping handles any length).

- Full-text view: sliced to start at Capítulo III (nothing before that is
  tagged). Each span is a nested <span> with its role color and an E# chip,
  so a reader can trace shared text back to its event.

All versions written by build_triples.py are rendered into the same page,
with a toggle at the top: "Inferred + literal" (triples.ann), "Full triples
(inferred + literal)" (triples_full.ann), "Literal
only" (triples_literal.ann) and "Full literal triples"
(triples_literal_full.ann). Element ids are prefixed per version
("inferred-E5", "literal-E5") because E/T numbering differs between them.
Each version's .jsonl supplies the statement number of every T, so spans
that belong to no event (their statement has no Deontic span in that
version) are marked "no deontic · St. N" instead of carrying no chip.
"""
from __future__ import annotations

import html
import json
import re
from collections import defaultdict

from v2_paths import (
    FULL_ANN_PATH,
    FULL_JSONL_PATH,
    LITERAL_ANN_PATH,
    LITERAL_FULL_ANN_PATH,
    LITERAL_FULL_JSONL_PATH,
    LITERAL_JSONL_PATH,
    TRIPLES_ANN_PATH,
    TRIPLES_JSONL_PATH,
    TRIPLES_TXT_PATH,
    TRIPLES_VIZ_HTML_PATH,
    V2_DIR,
)

ROOT = V2_DIR
TXT = TRIPLES_TXT_PATH
OUT = TRIPLES_VIZ_HTML_PATH

# (key, toggle label, .ann path, .jsonl path, one-line description shown above the cards)
MODES = [
    (
        "inferred",
        "Inferred + literal",
        TRIPLES_ANN_PATH,
        TRIPLES_JSONL_PATH,
        "Every span the matchers found, including ones inferred from a non-literal "
        "Excel value: bracketed values (“[Titulares de] Buses” → “buses”, "
        "“[deberá]” → “generará”), cross-references to an earlier sentence, "
        "and case/accent-folded matches. Deontic = the bold surface phrase.",
    ),
    (
        "full",
        "Full triples (inferred + literal)",
        FULL_ANN_PATH,
        FULL_JSONL_PATH,
        "Inferred + literal, restricted to statements that have an Attribute, a Deontic and "
        "an Object span: every event is a complete triple and every highlighted span belongs "
        "to one. Spans may still be inferred from non-literal Excel values.",
    ),
    (
        "literal",
        "Literal only",
        LITERAL_ANN_PATH,
        LITERAL_JSONL_PATH,
        "Only spans whose text is exactly the Excel value (whitespace aside), inside the "
        "statement’s own text. Deontic = the Excel modal itself (“deberán”, not "
        "“deberán contar”). Fewer spans and triples.",
    ),
    (
        "literal_full",
        "Full literal triples",
        LITERAL_FULL_ANN_PATH,
        LITERAL_FULL_JSONL_PATH,
        "Only statements whose Attribute, Deontic and Object are all literal: every event is "
        "a complete triple and every highlighted span belongs to one.",
    ),
]

TID_KEYS = ("attribute_tid", "deontic_tid", "object_tid")


def load_tid_to_stmt(jsonl_path):
    """T id -> Statement No., from build_triples.py's jsonl sidecar."""
    tid_to_stmt = {}
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            for key in TID_KEYS:
                if row[key]:
                    tid_to_stmt[row[key]] = row["statement_no"]
    return tid_to_stmt


def stmt_label(stmt_nos):
    return "St. " + ",".join(str(n) for n in sorted(set(stmt_nos))) if stmt_nos else ""

TLINE = re.compile(r"^(T\d+)\t(\S+) (\d+) (\d+)\t(.*)$")
ELINE = re.compile(r"^(E\d+)\t(.+)$")

# DirectObject is colored the same as Object and displayed under the generic
# "Object" label — they are the same role for the reader.
TYPE_COLORS = {
    "Deontic":      "#f6c177",
    "Attribute":    "#9ccfd8",
    "Object":       "#c4a7e7",
    "DirectObject": "#c4a7e7",
}
DEFAULT_COLOR = "#dcd7d2"

ROLE_ORDER = ("Attribute", "Deontic", "Object", "DirectObject")

# Capítulo III is where Attribute/Deontic/Object tagging actually begins;
# the earlier chapters are prelude and would render as plain, unmarked text.
CHAPTER_MARKER = "CAPÍTULO III"


def parse_ann(path):
    terms = {}
    events = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if m := TLINE.match(raw):
            tid, ttype, start, end, text = m.groups()
            terms[tid] = {"id": tid, "type": ttype,
                          "start": int(start), "end": int(end),
                          "text": text}
        elif m := ELINE.match(raw):
            eid, body = m.groups()
            roles: dict[str, list[str]] = defaultdict(list)
            trigger_role = trigger_tid = None
            for i, tok in enumerate(body.split()):
                role, tid = tok.split(":")
                roles[role].append(tid)
                if i == 0:
                    trigger_role, trigger_tid = role, tid
            events.append({"id": eid,
                           "trigger_role": trigger_role,
                           "trigger_tid": trigger_tid,
                           "roles": dict(roles)})
    return terms, events


def display_role(role):
    return "Object" if role == "DirectObject" else role


def role_color(role):
    return TYPE_COLORS.get(role, DEFAULT_COLOR)


def build_span_to_events(terms, events):
    """Group events by physical span (type, start, end).

    Each Attribute/Object occurrence gets its own T# in triples.ann even when
    two triples point at the exact same source text, so a plain tid-indexed
    lookup never shows that "fuentes estacionarias" is shared across E57–E59.
    Grouping by offsets makes that overlap visible.
    """
    key_to_events: dict[tuple, list[str]] = defaultdict(list)
    for ev in events:
        for tids in ev["roles"].values():
            for tid in tids:
                t = terms.get(tid)
                if t is None:
                    continue
                key = (t["type"], t["start"], t["end"])
                key_to_events[key].append(ev["id"])
    return key_to_events


def span_key(t):
    return (t["type"], t["start"], t["end"])


# --- Custom arc-diagram renderer -------------------------------------------
# Hand-rolled SVG instead of spaCy displacy so we can: show the full raw text
# as the pseudo-token (wrapping onto multiple lines), make per-token boxes
# variable width, draw round cubic-bezier arcs that scale with span distance,
# and label each token with "T# · Role" in grey below the box.

_CHAR_W      = 7.2    # ≈ Inter 13px avg char width
_TAG_CHAR_W  = 6.4    # Inter 11px
_LINE_H      = 18
_TAG_LINE_H  = 14
_TAG_GAP     = 6
_BOX_PAD_X   = 12
_BOX_PAD_Y   = 7
_TOKEN_GAP   = 32
_ARC_BASE_H  = 36
_ARC_PER_HOP = 22
_MAX_CHARS   = 32     # wrap target per visual line inside a token


def _wrap(text, max_chars=_MAX_CHARS):
    """Greedy word-wrap. Collapses whitespace first so brat newlines don't
    create empty lines."""
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


def render_event_arcs(ev, terms, id_prefix=""):
    """Build an SVG with one rounded box per role (full text, multi-line),
    a grey "T# · Role" caption below, and round bezier arcs from the trigger
    to each other role."""
    present = []
    for role, tids in ev["roles"].items():
        for tid in tids:
            t = terms.get(tid)
            if t is None:
                continue
            present.append((role, tid, t))
    present.sort(key=lambda rti: (rti[2]["start"], rti[2]["end"]))
    if not present:
        return ""

    # Lay out token boxes side by side.
    tokens = []
    x = _BOX_PAD_X
    for role, tid, t in present:
        role_disp = display_role(role)
        lines = _wrap(t["text"])
        tag = f"{tid} · {role_disp}"
        text_w = max(len(ln) for ln in lines) * _CHAR_W
        tag_w = len(tag) * _TAG_CHAR_W
        box_w = max(text_w, tag_w) + 2 * _BOX_PAD_X
        tokens.append({
            "tid": tid, "role": role, "role_disp": role_disp,
            "lines": lines, "tag": tag,
            "left_x": x, "box_w": box_w,
            "center_x": x + box_w / 2,
            "is_trigger": tid == ev["trigger_tid"],
        })
        x += box_w + _TOKEN_GAP
    total_w = x - _TOKEN_GAP + _BOX_PAD_X

    # Trigger-rooted arcs (left/right of the trigger).
    trigger_idx = next((i for i, tk in enumerate(tokens)
                        if tk["is_trigger"]), None)
    arcs = []
    if trigger_idx is not None:
        for i, tk in enumerate(tokens):
            if i == trigger_idx:
                continue
            lo, hi = sorted([trigger_idx, i])
            hops = hi - lo
            arcs.append({"lo": lo, "hi": hi,
                         "dest": i,
                         "label": tk["role_disp"],
                         "h": _ARC_BASE_H + (hops - 1) * _ARC_PER_HOP})
    max_arc_h = max((a["h"] for a in arcs), default=0)

    # Vertical layout: arcs on top, token boxes below, grey tag under box.
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

    # Arcs (behind boxes).
    arc_anchor_y = box_top_y  # arcs land on the top edge of each box
    for ai, arc in enumerate(arcs):
        x1 = tokens[arc["lo"]]["center_x"]
        x2 = tokens[arc["hi"]]["center_x"]
        y_top = arc_anchor_y - arc["h"]
        path_id = f'arc-{id_prefix}{ev["id"]}-{ai}'
        d = (f"M {x1:.1f},{arc_anchor_y:.1f} "
             f"C {x1:.1f},{y_top:.1f} {x2:.1f},{y_top:.1f} "
             f"{x2:.1f},{arc_anchor_y:.1f}")
        out.append(
            f'<path id="{path_id}" d="{d}" fill="none" '
            f'stroke="#9a9a9a" stroke-width="1.4"/>'
        )
        # Arrowhead at destination end only.
        dest_x = tokens[arc["dest"]]["center_x"]
        out.append(
            f'<path d="M {dest_x:.1f},{arc_anchor_y:.1f} '
            f'l -4,-7 l 8,0 z" fill="#9a9a9a"/>'
        )
        out.append(
            f'<text font-size="11" fill="#555">'
            f'<textPath xlink:href="#{path_id}" startOffset="50%" '
            f'text-anchor="middle" side="left">'
            f'{html.escape(arc["label"])}</textPath></text>'
        )

    # Token boxes + text.
    for tk in tokens:
        fill = role_color(tk["role"])
        stroke = "rgba(0,0,0,.35)" if tk["is_trigger"] else "rgba(0,0,0,.1)"
        stroke_w = 1.5 if tk["is_trigger"] else 1
        out.append(
            f'<rect x="{tk["left_x"]:.1f}" y="{box_top_y:.1f}" '
            f'width="{tk["box_w"]:.1f}" height="{box_h:.1f}" '
            f'rx="6" ry="6" fill="{fill}" fill-opacity=".55" '
            f'stroke="{stroke}" stroke-width="{stroke_w}"/>'
        )
        # Center the lines vertically within the box.
        text_block_h = len(tk["lines"]) * _LINE_H
        first_baseline = (box_top_y + (box_h - text_block_h) / 2
                          + _LINE_H - 5)
        out.append(f'<text text-anchor="middle" fill="#1b1b1b">')
        for li, line in enumerate(tk["lines"]):
            y = first_baseline + li * _LINE_H
            out.append(
                f'<tspan x="{tk["center_x"]:.1f}" y="{y:.1f}">'
                f'{html.escape(line)}</tspan>'
            )
        out.append('</text>')
        # Grey T# · Role caption underneath.
        out.append(
            f'<text text-anchor="middle" font-size="11" '
            f'fill="#7a7a7a" font-family="ui-monospace, monospace" '
            f'x="{tk["center_x"]:.1f}" y="{tag_y:.1f}">'
            f'{html.escape(tk["tag"])}</text>'
        )

    out.append('</svg>')
    return f'<div class="arc-view">{"".join(out)}</div>'


def render_event_card(ev, terms, span_to_events, id_prefix="", tid_to_stmt=None):
    pairs = []
    seen_roles = set()
    for role in ROLE_ORDER:
        for tid in ev["roles"].get(role, []):
            pairs.append((role, tid))
            seen_roles.add(role)
    for role, tids in ev["roles"].items():
        if role in seen_roles:
            continue
        for tid in tids:
            pairs.append((role, tid))

    rows = []
    for role, tid in pairs:
        t = terms.get(tid)
        if t is None:
            continue
        peers = [e for e in span_to_events.get(span_key(t), [])
                 if e != ev["id"]]
        shared = (f' <span class="shared">mismo texto también en '
                  f'{", ".join(sorted(set(peers), key=_eid_sort))}</span>'
                  if peers else "")
        rows.append(
            '<div class="row">'
            f'<div class="role-chip" style="background:{role_color(role)}">'
            f'{display_role(role)}</div>'
            '<div class="row-body">'
            f'<div class="row-meta">{tid}'
            f' <span class="offs">[{t["start"]}&ndash;{t["end"]}]</span>'
            f'{shared}</div>'
            f'<div class="row-text">{html.escape(t["text"].strip())}</div>'
            '</div></div>'
        )

    trig_term = terms.get(ev["trigger_tid"], {})
    anchor_id = f'{id_prefix}{ev["id"]}'
    stmt_no = (tid_to_stmt or {}).get(ev["trigger_tid"])
    stmt = (f'<span class="muted stmt">{stmt_label([stmt_no])}</span>'
            if stmt_no is not None else "")
    header = (
        f'<h3 id="{anchor_id}">'
        f'<a class="anchor" href="#{anchor_id}">{ev["id"]}</a>{stmt}'
        f'<span class="muted"> — {display_role(ev["trigger_role"])}:</span> '
        f'<span class="trig-text">'
        f'{html.escape(trig_term.get("text", "").strip())}</span></h3>'
    )
    arcs = render_event_arcs(ev, terms, id_prefix)
    return (f'<section class="event-card">{header}'
            f'{arcs}{"".join(rows)}</section>')


def build_event_cards(events, terms, span_to_events, id_prefix="",
                      tid_to_stmt=None):
    return "".join(render_event_card(ev, terms, span_to_events, id_prefix,
                                     tid_to_stmt)
                   for ev in events)


def _eid_sort(eid):
    m = re.match(r"E(\d+)", eid)
    return int(m.group(1)) if m else 0


def slice_from_chapter_iii(text):
    idx = text.find(CHAPTER_MARKER)
    if idx < 0:
        return text, 0
    return text[idx:], idx


def render_annotated_text(text, terms, offset, span_to_events, tid_to_stmt,
                          tids_in_events):
    """Highlight each physical span in `text` with its role color + E# chip.

    Spans are deduplicated by (type, start, end): identical re-tagging (e.g.
    the 15 Attribute T#s on "Superintendencia del Medio Ambiente") collapses
    into one highlighted range, and the chip lists every event that uses it.
    T#s of that range that are in no event (their statement has no Deontic
    span in this version) get a "no deontic · St. N" chip instead.
    Overlapping spans nest with the classic split-and-reopen technique so
    the HTML is valid even when a longer span contains a shorter one.
    """
    unique: dict[tuple, dict] = {}
    for t in terms.values():
        if t["start"] < offset or t["end"] > offset + len(text):
            continue
        unique.setdefault(span_key(t), {
            "type": t["type"],
            "start": t["start"],
            "end": t["end"],
            "tids": [],
        })["tids"].append(t["id"])
    spans = list(unique.values())

    boundaries = []
    for s in spans:
        boundaries.append((s["start"] - offset, 1, s))
        boundaries.append((s["end"] - offset, 0, s))
    boundaries.sort(key=lambda e: (
        e[0],
        e[1],
        -(e[2]["end"] - e[2]["start"]) if e[1] == 1
        else (e[2]["end"] - e[2]["start"]),
    ))

    def _events_for(s):
        return sorted(set(span_to_events.get(
            (s["type"], s["start"], s["end"]), [])), key=_eid_sort)

    def _no_deontic(s):
        """Label for this range's T#s that belong to no event, or ""."""
        orphans = [tid for tid in s["tids"] if tid not in tids_in_events]
        if not orphans:
            return ""
        return " · ".join(filter(None, [
            "no deontic", stmt_label([tid_to_stmt[t] for t in orphans
                                      if t in tid_to_stmt])]))

    def open_tag(s):
        role_disp = display_role(s["type"])
        eids = _events_for(s)
        eid_str = " · ".join(filter(None, [",".join(eids), _no_deontic(s)]))
        tids = ",".join(s["tids"])
        title = f'{tids} · {role_disp} · {eid_str}'
        return (f'<span class="ann" style="background:{role_color(s["type"])}"'
                f' title="{html.escape(title)}">')

    def close_tag(s, final):
        if not final:
            return "</span>"
        eids = _events_for(s)
        chip = (f'<sup class="eid">{",".join(eids)}</sup>'
                if eids else '')
        no_deontic = _no_deontic(s)
        if no_deontic:
            chip += f'<sup class="eid no-deontic">{html.escape(no_deontic)}</sup>'
        return f'{chip}</span>'

    out: list[str] = []
    stack: list[dict] = []
    pos = 0
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
  .legend {{ margin: .5rem 0 1.5rem; display: flex; gap: 8px;
             flex-wrap: wrap; align-items: center; }}
  .chip {{ display: inline-block; padding: 2px 10px; border-radius: 10px;
           font-size: 12px; }}

  /* --- Per-event cards --- */
  .event-card {{ border: 1px solid #ececec; border-radius: 8px;
                 padding: .75rem 1rem; margin: .75rem 0; background: #fff; }}
  .event-card h3 {{ display: flex; gap: 6px; align-items: baseline;
                     flex-wrap: wrap; }}
  .event-card h3 .anchor {{ color: #555; text-decoration: none;
                             font-family: ui-monospace, monospace;
                             font-size: 12px; }}
  .event-card h3 .trig-text {{ font-weight: 600; }}
  .row {{ display: grid; grid-template-columns: 110px 1fr;
          gap: .5rem 1rem; margin-top: .5rem; align-items: start; }}
  .role-chip {{ font-size: 11px; text-align: center;
                padding: 3px 8px; border-radius: 6px;
                font-weight: 600; color: #1b1b1b; }}
  .row-body {{ min-width: 0; }}
  .row-meta {{ color: #666; font-size: 12px;
               font-family: ui-monospace, monospace; }}
  .row-meta .offs {{ color: #999; }}
  .row-meta .shared {{ color: #888; margin-left: 6px;
                        font-family: Inter, sans-serif; font-style: italic; }}
  .row-text {{ font-size: 14px; word-wrap: break-word; }}

  /* Per-event arc diagram (hand-rolled SVG). */
  .arc-view {{ margin: .5rem 0 .75rem; overflow-x: auto;
               padding-bottom: 4px; }}
  .arc-view svg.arc-svg {{ display: block; }}

  /* --- Annotated-text view --- */
  .passage {{ line-height: 2.3; font-size: 15px;
              white-space: pre-wrap; }}
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
  .passage .ann sup.no-deontic {{ font-family: Inter, system-ui, sans-serif;
                                   font-style: italic; color: #555;
                                   background: rgba(255,255,255,.8);
                                   border: 1px dashed #999; }}
  .event-card h3 .stmt {{ font-family: ui-monospace, monospace;
                          font-size: 12px; }}

  /* --- Version toggle --- */
  .toggle {{ display: inline-flex; border: 1px solid #d6d6d6;
             border-radius: 8px; overflow: hidden; margin: .25rem 0 .5rem; }}
  .toggle label {{ padding: 6px 14px; font-size: 13px; cursor: pointer;
                   user-select: none; }}
  .toggle label + label {{ border-left: 1px solid #d6d6d6; }}
  .toggle input {{ position: absolute; opacity: 0; pointer-events: none; }}
  .toggle label:has(input:checked) {{ background: #1b1b1b; color: #fff; }}
  .toggle label:has(input:focus-visible) {{ outline: 2px solid #4a7bd0;
                                            outline-offset: -2px; }}
  .mode-desc {{ max-width: 760px; font-size: 13px; }}
</style></head><body>
<h1>Triples — DTO-31_24</h1>
<div class="toggle" role="radiogroup" aria-label="Version">{toggle}</div>
<div class="legend">{legend}</div>
{bodies}
<script>{script}</script>
</body></html>
"""

MODE_BODY = """<section class="mode" data-mode="{mode}"{hidden}>
<p class="muted mode-desc">{description}</p>
<p class="muted">{n_events} events · {n_terms} T-spans ({n_no_deontic} with no deontic) · text sliced from Capítulo III</p>

<h2>Per-event cards <span class="muted">({n_events})</span></h2>
{cards}

<h2>Full text with inline spans</h2>
<p class="muted">Hover a span to see its T#, role, and event ID; the small
superscript next to each span is the E# it belongs to (comma-separated when
the same text is reused by multiple events). A dashed <i>no deontic · St. N</i>
chip marks spans of statement N that have no Deontic span in this version,
so they are in no event.</p>
<div class="passage">{passage}</div>
</section>
"""

# Shows one .mode section at a time. A "#literal-E5"-style hash picks its
# version; otherwise the last choice is remembered (per browser, best effort).
TOGGLE_SCRIPT = """
(function () {
  var KEY = "triples-viz-mode";
  var radios = Array.prototype.slice.call(document.querySelectorAll('input[name="mode"]'));
  function show(mode) {
    document.querySelectorAll(".mode").forEach(function (el) {
      el.hidden = el.getAttribute("data-mode") !== mode;
    });
    try { localStorage.setItem(KEY, mode); } catch (e) {}
  }
  var wanted = null;
  var m = location.hash.match(/^#(\\w+)-E\\d+$/);
  if (m) { wanted = m[1]; } else { try { wanted = localStorage.getItem(KEY); } catch (e) {} }
  radios.forEach(function (r) {
    if (r.value === wanted) { r.checked = true; }
    r.addEventListener("change", function () { if (r.checked) { show(r.value); } });
  });
  var checked = radios.filter(function (r) { return r.checked; })[0] || radios[0];
  checked.checked = true;
  show(checked.value);
  if (m) { var target = document.getElementById(location.hash.slice(1)); if (target) { target.scrollIntoView(); } }
})();
"""


def build_mode_body(mode, description, events, terms, tid_to_stmt, text,
                    offset, hidden):
    span_to_events = build_span_to_events(terms, events)
    tids_in_events = {tid for ev in events for tids in ev["roles"].values()
                      for tid in tids}
    cards = build_event_cards(events, terms, span_to_events,
                              id_prefix=f"{mode}-", tid_to_stmt=tid_to_stmt)
    passage = render_annotated_text(text, terms, offset, span_to_events,
                                    tid_to_stmt, tids_in_events)
    in_slice = [t for t in terms.values() if t["start"] >= offset]
    return MODE_BODY.format(
        mode=mode,
        hidden=" hidden" if hidden else "",
        description=html.escape(description),
        n_events=len(events),
        n_terms=len(in_slice),
        n_no_deontic=sum(1 for t in in_slice if t["id"] not in tids_in_events),
        cards=cards,
        passage=passage,
    )


def build_html(versions, text, offset):
    """`versions` is [(mode, label, description, events, terms,
    tid_to_stmt)]; the first one is shown by default."""
    legend_items = [(k, v) for k, v in TYPE_COLORS.items()
                    if k != "DirectObject"]
    legend = " ".join(
        f'<span class="chip" style="background:{c}">{display_role(k)}</span>'
        for k, c in legend_items
    )
    toggle = "".join(
        f'<label><input type="radio" name="mode" value="{mode}"'
        f'{" checked" if i == 0 else ""}> {html.escape(label)} '
        f'<span class="muted">({len(events)})</span></label>'
        for i, (mode, label, _, events, _, _) in enumerate(versions)
    )
    bodies = "".join(
        build_mode_body(mode, description, events, terms, tid_to_stmt, text,
                        offset, hidden=i > 0)
        for i, (mode, _, description, events, terms, tid_to_stmt)
        in enumerate(versions)
    )
    return HTML_SHELL.format(toggle=toggle, legend=legend, bodies=bodies,
                             script=TOGGLE_SCRIPT)


def main():
    raw_text = TXT.read_text(encoding="utf-8")
    text, offset = slice_from_chapter_iii(raw_text)
    versions = []
    for mode, label, ann_path, jsonl_path, description in MODES:
        terms, events = parse_ann(ann_path)
        versions.append((mode, label, description, events, terms,
                         load_tid_to_stmt(jsonl_path)))
        print(f"{mode}: {len(events)} events, {len(terms)} spans "
              f"({ann_path.relative_to(ROOT.parent)})")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_html(versions, text, offset), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT.parent)}  "
          f"(text starts at offset {offset})")


if __name__ == "__main__":
    main()
