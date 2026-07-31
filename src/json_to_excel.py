import json
from pathlib import Path
import pandas as pd
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Font, PatternFill

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
INPUT_FILE = OUTPUT_DIR / "extraction_results.json"
OUTPUT_FILE = OUTPUT_DIR / "extraction_results.xlsx"
SHEET_NAME = "Statements"

# Preferred column order (IG framework grouping). Any unexpected keys are
# appended at the end so nothing is silently dropped.
COLUMN_ORDER = [
    "Section Marker",
    "Statement No.",
    "Raw Statement",
    "Statement Type",
    "Attribute",
    "Attribute Property",
    "Deontic",
    "Aim",
    "Direct Object (Content)",
    "Direct Object Property",
    "Indirect Object (Content)",
    "Activation Condition (Content)",
    "Execution Constraint (Content)",
    "Constituted Entity",
    "Constituting Function",
    "Constituted Properties",
    "Function",
    "Logical combination",
    "Invoking statement(s)",
]

# Per-column widths (chars). Long free-text fields get more room.
COLUMN_WIDTHS = {
    "Section Marker": 32,
    "Statement No.": 8,
    "Raw Statement": 70,
    "Statement Type": 14,
    "Attribute": 28,
    "Attribute Property": 40,
    "Deontic": 12,
    "Aim": 16,
    "Direct Object (Content)": 32,
    "Direct Object Property": 40,
    "Indirect Object (Content)": 32,
    "Activation Condition (Content)": 50,
    "Execution Constraint (Content)": 40,
    "Constituted Entity": 32,
    "Constituting Function": 24,
    "Constituted Properties": 50,
    "Function": 20,
    "Logical combination": 18,
    "Invoking statement(s)": 14,
}
DEFAULT_WIDTH = 25


def load_records(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def order_columns(records: list[dict]) -> list[str]:
    seen = {k for r in records for k in r.keys()}
    ordered = [c for c in COLUMN_ORDER if c in seen]
    extras = sorted(seen - set(ordered))
    return ordered + extras


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records = load_records(INPUT_FILE)
    columns = order_columns(records)
    df = pd.DataFrame(records).reindex(columns=columns)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=SHEET_NAME)
        ws = writer.sheets[SHEET_NAME]

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        body_align = Alignment(vertical="top", wrap_text=True)

        for col_idx, name in enumerate(df.columns, start=1):
            letter = get_column_letter(col_idx)
            ws.column_dimensions[letter].width = COLUMN_WIDTHS.get(name, DEFAULT_WIDTH)
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align

        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=ws.max_column):
            for cell in row:
                cell.alignment = body_align

        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    print(f"Wrote {len(df)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
