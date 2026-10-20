"""Call DOGE's direction after a Musk post with the saved models (models/musk_doge_direction_*d.json).

    python scripts/predict.py "Dogecoin is the people's crypto" --at 2021-02-04T08:00:00Z
    python scripts/predict.py "Doge to the moon" "Much wow" --at 2021-05-08T20:00:00Z --horizon 1 3

Several texts with one --at are treated as posts on the same day. The DOGE prices in data/raw/prices/ must cover the
post's anchor close; if they also cover the horizon, the actual move is printed next to the call.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from dogebone.model import Predictor  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("text", nargs="+", help="post text (quote it); several = several posts on the same day")
    ap.add_argument("--at", required=True, help="UTC time of the post, e.g. 2021-12-14T10:00:00Z")
    ap.add_argument("--horizon", type=int, nargs="*", help="horizons in days (default: every saved model)")
    ap.add_argument("--model-dir", type=Path, default=ROOT / "models")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    try:
        out = Predictor.from_repo(args.model_dir).predict(args.text, posted_at=args.at, horizons=args.horizon)
    except (ValueError, FileNotFoundError) as e:
        sys.exit(f"error: {e}")
    for r in out.itertuples():
        actual = "" if r.actual is None else f"  | actual: {r.actual} ({r.actual_return:+.1%})"
        print(f"{r.horizon_d}d after the {pd.Timestamp(r.anchor_date):%Y-%m-%d} close: {r.direction}, "
              f"P(up) = {r.p_up:.0%}, conviction {r.conviction}{actual}")
        print(f"    why: {r.top_reasons}")
    terms = out["matched_terms"].iloc[0] if len(out) else ""
    print(f"lexicon sentiment {out['lexicon_sentiment'].iloc[0]:+.2f}; matched terms: {terms or 'none'}")


if __name__ == "__main__":
    main()
