import re

from document_extractor import get_document_text
from paths import TRAINING_LITERALS_ANN_PATH

TLINE_RE = re.compile(r"^T(\d+)\t\w+ \d+ \d+\t(.*)$")


def main():
    doc = get_document_text()
    found = 0
    max_id = 0
    with open(TRAINING_LITERALS_ANN_PATH, encoding="utf-8") as f:
        for line in f:
            m = TLINE_RE.match(line.rstrip("\n"))
            if not m:
                continue
            i = int(m.group(1))
            text = m.group(2)
            if i > max_id:
                max_id = i
            found += 1 if text in doc else 0
    print(f"max T-id: {max_id}")
    print(f"found:    {found}")


if __name__ == "__main__":
    main()
