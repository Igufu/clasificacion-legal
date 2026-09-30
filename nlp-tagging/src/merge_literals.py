"""Merge Attribute + Deontic + Object literal annotations into one file.

Reads T-lines and R-lines from:
  - outputs/annotations/deontic_literal.ann  (Attribute + Deontic literals)
  - outputs/annotations/objects.ann          (DirectObject, IndirectObject,
                                              DirectObjectProperty,
                                              IndirectObjectProperty, plus
                                              PropertyOf R-lines)

Writes them to outputs/annotations/training_literals.ann with fresh
sequential T-ids and R-ids. Each annotation's (label, start, end, text) is
preserved verbatim; R-line Arg1/Arg2 references are rewritten to the new
T-ids via a per-source id map.
"""

import re

from paths import (
    DEONTIC_LITERAL_ANN_PATH,
    OBJECTS_ANN_PATH,
    TRAINING_LITERALS_ANN_PATH,
    ensure_outputs_dir,
)

TLINE_RE = re.compile(r"^T(\d+)\t(\w+) (\d+) (\d+)\t(.*)$")
RLINE_RE = re.compile(r"^R\d+\t(\w+) Arg1:T(\d+) Arg2:T(\d+)$")


def main():
    ensure_outputs_dir()
    sources = [DEONTIC_LITERAL_ANN_PATH, OBJECTS_ANN_PATH]

    counts = {}
    t_lines = []
    tid_maps = {}
    tid = 1

    for path in sources:
        tid_map = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = TLINE_RE.match(line.rstrip("\n"))
                if not m:
                    continue
                old_tid = int(m.group(1))
                label, start, end, text = m.group(2), m.group(3), m.group(4), m.group(5)
                tid_map[old_tid] = tid
                t_lines.append(f"T{tid}\t{label} {start} {end}\t{text}")
                counts[label] = counts.get(label, 0) + 1
                tid += 1
        tid_maps[path] = tid_map

    r_lines = []
    rid = 1
    for path in sources:
        tid_map = tid_maps[path]
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = RLINE_RE.match(line.rstrip("\n"))
                if not m:
                    continue
                rel, a, b = m.group(1), int(m.group(2)), int(m.group(3))
                r_lines.append(
                    f"R{rid}\t{rel} Arg1:T{tid_map[a]} Arg2:T{tid_map[b]}"
                )
                rid += 1

    with open(TRAINING_LITERALS_ANN_PATH, "w", encoding="utf-8", newline="") as f:
        for line in t_lines:
            f.write(line + "\n")
        for line in r_lines:
            f.write(line + "\n")

    print(f"Sources: {[p.name for p in sources]}")
    print(
        f"T-lines: {tid - 1}, R-lines: {rid - 1} "
        f"-> {TRAINING_LITERALS_ANN_PATH.name}"
    )
    for label, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {label}: {n}")


if __name__ == "__main__":
    main()
