"""Render triples.ann as two spaCy displacy views.

- Dep view: one SVG per event. Each Deontic/Attribute/Object span is a single
  pseudo-token (span text verbatim); arcs go Deontic -> Attribute / Object.
- Span view: full triples.txt with every T span highlighted by type.
Outputs a single HTML at v2_triples/reports/triples_viz.html.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

import spacy
from spacy.tokens import Span
from spacy import displacy

ROOT = Path(__file__).resolve().parents[1]
ANN = ROOT / "data" / "triples.ann"
TXT = ROOT / "data" / "triples.txt"
OUT = ROOT / "reports" / "triples_viz.html"

TLINE = re.compile(r"^(T\d+)\t(\S+) (\d+) (\d+)\t(.*)$")
ELINE = re.compile(r"^(E\d+)\t(.+)$")

TYPE_COLORS = {
    "Deontic": "#f6c177",
    "Attribute": "#9ccfd8",
    "Object": "#c4a7e7",
}
ROLE_ORDER = ("Attribute", "Deontic", "Object")  # left-to-right display


def parse_ann(path: Path):
    terms: dict[str, dict] = {}
    events: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if m := TLINE.match(raw):
            tid, ttype, start, end, text = m.groups()
            terms[tid] = {"id": tid, "type": ttype, "start": int(start),
                          "end": int(end), "text": text}
        elif m := ELINE.match(raw):
            eid, body = m.groups()
            roles: dict[str, str] = {}
            trigger_role = None
            trigger_tid = None
            for tok in body.split():
                role, tid = tok.split(":")
                roles[role] = tid
                if trigger_role is None:  # first token is the trigger per BRAT
                    trigger_role, trigger_tid = role, tid
            events.append({"id": eid, "trigger_role": trigger_role,
                           "trigger_tid": trigger_tid, "roles": roles})
    return terms, events


def shorten(text: str, limit: int = 70) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render_event(event: dict, terms: dict[str, dict]) -> str:
    """One displacy manual-dep SVG per event. Each T span is one pseudo-token."""
    present = [(role, event["roles"][role]) for role in ROLE_ORDER
               if role in event["roles"]]
    present.sort(key=lambda rt: terms[rt[1]]["start"])  # keep text order

    words = [{"text": shorten(terms[tid]["text"]), "tag": role}
             for role, tid in present]
    trigger_idx = next((i for i, (role, _) in enumerate(present)
                        if role == event["trigger_role"]), None)

    arcs = []
    if trigger_idx is not None:
        for i, (role, _) in enumerate(present):
            if i == trigger_idx:
                continue
            lo, hi = sorted([trigger_idx, i])
            arcs.append({"start": lo, "end": hi, "label": role,
                         "dir": "right" if i > trigger_idx else "left"})

    svg = displacy.render(
        {"words": words, "arcs": arcs},
        style="dep", manual=True, page=False,
        options={"compact": True, "distance": 140, "color": "#333",
                 "bg": "#fafafa", "font": "Inter, system-ui, sans-serif"},
    )
    return svg


def render_spans(terms: dict[str, dict], text: str) -> str:
    """Full-text span view with every T span highlighted."""
    nlp = spacy.blank("es")
    doc = nlp(text)
    spans: list[Span] = []
    for t in terms.values():
        s = doc.char_span(t["start"], t["end"], label=t["type"],
                          alignment_mode="expand")
        if s is not None:
            spans.append(s)
    doc.spans["sc"] = spans
    return displacy.render(
        doc, style="span", page=False,
        options={"spans_key": "sc", "colors": TYPE_COLORS},
    )


def build_html(events: list[dict], terms: dict[str, dict], text: str) -> str:
    legend = " ".join(
        f'<span class="chip" style="background:{c}">{k}</span>'
        for k, c in TYPE_COLORS.items()
    )

    event_blocks = []
    for ev in events:
        trig = terms.get(ev["trigger_tid"], {})
        header = (f'<h3>{ev["id"]} &middot; '
                  f'<span class="muted">{ev["trigger_role"]}:</span> '
                  f'{html.escape(shorten(trig.get("text", ""), 90))}</h3>')
        event_blocks.append(f'<section class="event">{header}'
                            f'{render_event(ev, terms)}</section>')

    span_view = render_spans(terms, text)

    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>Triples visualization &mdash; DTO-31_24</title>
<style>
  body {{ font-family: Inter, system-ui, sans-serif; margin: 2rem auto;
          max-width: 1100px; color: #222; }}
  h1 {{ margin-bottom: .25rem; }}
  .legend {{ margin: .5rem 0 1.5rem; }}
  .chip {{ display: inline-block; padding: 2px 10px; border-radius: 10px;
           margin-right: 6px; font-size: 12px; }}
  .muted {{ color: #777; font-weight: normal; }}
  section.event {{ border-top: 1px solid #eee; padding: 1rem 0; }}
  section.event h3 {{ margin: 0 0 .5rem; font-size: 14px; }}
  details > summary {{ cursor: pointer; font-weight: 600; margin: 1rem 0; }}
  .span-view {{ line-height: 2.2; }}
</style></head><body>
<h1>Triples &mdash; DTO-31_24</h1>
<p class="muted">{len(events)} events over {len(terms)} T spans.</p>
<div class="legend">{legend}</div>

<details open><summary>Per-event dep view ({len(events)})</summary>
{''.join(event_blocks)}
</details>

<details><summary>Full-text span view</summary>
<div class="span-view">{span_view}</div>
</details>
</body></html>
"""


def main() -> None:
    terms, events = parse_ann(ANN)
    text = TXT.read_text(encoding="utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_html(events, terms, text), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT.parent)}  "
          f"({len(events)} events, {len(terms)} spans)")


if __name__ == "__main__":
    main()
