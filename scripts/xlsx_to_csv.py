"""Convert a simple .xlsx sheet to CSV using only the standard library (no openpyxl needed).

    python scripts/xlsx_to_csv.py data/raw/prices/DogePrice.xlsx data/raw/prices/doge_daily_2021.csv

Excel date serials in date-like columns are converted to ISO dates.
"""

from __future__ import annotations

import csv
import re
import sys
import zipfile
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
EXCEL_EPOCH = datetime(1899, 12, 30)


def col_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_sheet(path: str, sheet: int = 1) -> list[list[str]]:
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")) for si in root.findall("m:si", NS)]
        root = ET.fromstring(z.read(f"xl/worksheets/sheet{sheet}.xml"))
    rows = []
    for row in root.iter(f"{{{NS['m']}}}row"):
        cells = {}
        for c in row.findall("m:c", NS):
            v = c.find("m:v", NS)
            if c.get("t") == "inlineStr":
                text = "".join(t.text or "" for t in c.iter(f"{{{NS['m']}}}t"))
            elif v is None:
                continue
            elif c.get("t") == "s":
                text = shared[int(v.text)]
            else:
                text = v.text
            cells[col_index(c.get("r"))] = text
        if cells:
            rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
    return rows


def excel_date(value: str) -> str:
    try:
        return (EXCEL_EPOCH + timedelta(days=float(value))).strftime("%Y-%m-%d")
    except ValueError:
        return value  # already text


def main(src: str, dst: str) -> None:
    rows = read_sheet(src)
    header = rows[0]
    date_cols = [i for i, h in enumerate(header) if re.search(r"date|time|day", str(h), re.IGNORECASE)]
    with open(dst, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows[1:]:
            r = r + [""] * (len(header) - len(r))
            w.writerow([excel_date(v) if i in date_cols and v else v for i, v in enumerate(r)])
    print(f"Wrote {len(rows) - 1} rows x {len(header)} columns to {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
