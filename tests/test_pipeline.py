"""Fast checks for the rules most likely to silently break. Run: python -m pytest tests  (or: python tests/test_pipeline.py)"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dogebone import Config  # noqa: E402
from dogebone.lexicon import LexiconScorer  # noqa: E402
from dogebone.market import anchor_dates, forward_returns  # noqa: E402

CFG = Config()
SCORER = LexiconScorer(CFG)


def terms(text):
    return [t for t, _ in SCORER.score(text).hits]


def test_longest_phrase_wins():
    assert terms("this is a pump and dump") == ["pump and dump"]
    assert terms("buy the dip") == ["buy the dip"]


def test_negation_flips():
    assert SCORER.score("DOGE is not bullish").sentiment < 0
    assert SCORER.score("not selling my dogecoin").sentiment > 0


def test_modifiers_do_not_leak_past_previous_term():
    hits = dict(SCORER.score("extremely bullish 🚀").hits)
    assert hits["🚀"] == 2.5  # 'extremely' modifies 'bullish' only


def test_hedges_and_fancy_unicode():
    assert abs(SCORER.score("maybe dogecoin could rally?").sentiment) < abs(SCORER.score("dogecoin rally").sentiment)
    assert terms("𝐃𝐎𝐆𝐄 is moooooning 🚀") == ["mooning", "🚀"]


def test_nearest_close_anchoring():
    ts = pd.Series(pd.to_datetime(["2021-05-09 03:30", "2021-05-09 20:00"], utc=True))
    a = anchor_dates(ts, CFG)
    assert list(a) == [pd.Timestamp("2021-05-08"), pd.Timestamp("2021-05-09")]


def test_forward_returns_have_no_look_ahead():
    px = pd.DataFrame({"close": [1.0, 2.0, 4.0, 8.0]}, index=pd.date_range("2021-01-01", periods=4))
    r = forward_returns(px, (1,))
    assert r.loc["2021-01-01", "fwd_ret_1d"] == 1.0  # 1 -> 2
    assert r.loc["2021-01-02", "mom_1d"] == 1.0  # 1 -> 2, known at the anchor close
    assert pd.isna(r.loc["2021-01-04", "fwd_ret_1d"])


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
