"""Turn the team's DogePrice.xlsx (day index + daily OPEN price) into the pipeline's daily price CSV.

    python scripts/prepare_doge_prices.py

Source: data/raw/prices/DogePrice.xlsx, columns [blank, "Date" = day index 1..730, "Opening price", daily % change].
Day 1 = 2021-01-01, validated against known moves (Jan 28->29 2021 WSB spike, May 8 2021 all-time-high open, the
Apr 25 2022 Twitter-deal jump).

Crypto trades 24/7, so the open on day D equals the close on day D-1. We write close[D] = open[D+1], which drops the
last day (no next open). Output: data/raw/prices/doge_daily.csv with columns date, open, close.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from xlsx_to_csv import read_sheet  # noqa: E402

SRC = ROOT / "data" / "raw" / "prices" / "DogePrice.xlsx"
DST = ROOT / "data" / "raw" / "prices" / "doge_daily.csv"
DAY1 = "2021-01-01"


def main() -> None:
    rows = read_sheet(str(SRC))
    header, body = rows[0], rows[1:]
    day_col, open_col = header.index("Date"), header.index("Opening price")
    days = [int(float(r[day_col])) for r in body]
    if days != list(range(1, len(days) + 1)):
        raise ValueError("Day index is not a gap-free 1..N sequence; check the workbook.")
    opens = pd.Series([float(r[open_col]) for r in body], index=pd.date_range(DAY1, periods=len(body), freq="D"))
    out = pd.DataFrame({"open": opens, "close": opens.shift(-1)}).dropna()
    out.index.name = "date"
    out.to_csv(DST, float_format="%.8f")
    print(f"Wrote {len(out)} days ({out.index[0]:%Y-%m-%d} to {out.index[-1]:%Y-%m-%d}) to {DST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
