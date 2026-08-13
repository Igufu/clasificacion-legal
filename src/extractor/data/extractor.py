import json
from pathlib import Path

DATA_PATH = Path(__file__).parent / "original_extracts.json"


def main():
    with open(DATA_PATH, encoding="utf-8") as f:
        entries = json.load(f)

    trimmed = [
        {"Statement No.": entry["Statement No."], "Raw Statement": entry["Raw Statement"]}
        for entry in entries
    ]

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
