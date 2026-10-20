"""Fast checks for the rules most likely to silently break. Run: python -m pytest tests  (or: python tests/test_pipeline.py)"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dogebone import Config  # noqa: E402
from dogebone.lexicon import LexiconScorer  # noqa: E402
from dogebone.market import anchor_dates, forward_returns  # noqa: E402
from dogebone import model as M  # noqa: E402
import numpy as np  # noqa: E402

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


def test_model_features_ignore_future_prices():
    px = pd.Series(np.linspace(1, 2, 60), index=pd.date_range("2021-01-01", periods=60))
    bumped = px.copy()
    bumped.iloc[40:] *= 3  # change only the future
    a, b = M.market_features(px), M.market_features(bumped)
    cols = ["mom_1d", "mom_7d", "vol_7d", "dd_30d"]
    pd.testing.assert_frame_equal(a.loc[:"2021-02-09", cols], b.loc[:"2021-02-09", cols])


def test_training_rows_never_overlap_the_test_period():
    ev = pd.DataFrame({"anchor_date": pd.date_range("2021-08-20", periods=15)})
    keep = ev[M.train_mask(ev, 7, "2021-09-01")]
    assert (keep["anchor_date"] + pd.Timedelta(days=7) < pd.Timestamp("2021-09-01")).all()
    assert keep["anchor_date"].max() == pd.Timestamp("2021-08-24")  # outcome close 08-31 is known before 09-01


def test_logistic_regression_reaches_penalized_optimum():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(200, 2))
    y = (rng.random(200) < 1 / (1 + np.exp(-(0.3 + 1.5 * x[:, 0])))).astype(float)
    ev = pd.DataFrame({"a": x[:, 0], "b": x[:, 1], "y_1d": y, "anchor_date": pd.date_range("2021-01-01", periods=200)})
    m = M.DirectionModel(1, ["a", "b"], l2=2.0).fit(ev)
    z = (x - m.mean_) / m.scale_
    p = 1 / (1 + np.exp(-(m.intercept_ + z @ m.coef_)))
    grad = np.r_[np.sum(p - y), z.T @ (p - y) + 2.0 * m.coef_]
    assert np.abs(grad).max() < 1e-6
    assert m.coef_[0] > 1.0 and abs(m.coef_[1]) < 0.3


def test_walk_forward_is_purged_and_predicts_each_day_once():
    rng = np.random.default_rng(1)
    dates = pd.date_range("2021-01-01", "2021-06-30", freq="2D")
    ev = pd.DataFrame({"anchor_date": dates, "a": rng.normal(size=len(dates)), "mom_3d": 0.0})
    ev["y_3d"] = (rng.random(len(dates)) < 0.5).astype(float)
    ev["fwd_ret_3d"] = ev["y_3d"] - 0.5
    preds = M.walk_forward(ev, 3, ["a"], first_test="2021-03-01")
    assert preds["anchor_date"].is_unique and preds["anchor_date"].min() >= pd.Timestamp("2021-03-01")
    for fold, g in preds.groupby("fold"):
        start = pd.Timestamp(f"{fold}-01")
        assert (g["anchor_date"] >= start).all() and (g["anchor_date"] < start + pd.offsets.MonthBegin(1)).all()
        assert g["n_train"].iloc[0] == int((ev["anchor_date"] + pd.Timedelta(days=3) < start).sum())


def test_saved_model_round_trips_and_predictor_guards_dates():
    import tempfile

    rng = np.random.default_rng(2)
    ev = pd.DataFrame({f: rng.normal(size=60) for f in M.ALL_FEATURES})
    ev["anchor_date"] = pd.date_range("2021-02-01", periods=60)
    ev["y_1d"] = (rng.random(60) < 0.5).astype(float)
    m = M.DirectionModel(1).fit(ev)
    with tempfile.TemporaryDirectory() as d:
        m2 = M.DirectionModel.load(m.save(Path(d) / "m.json"))
    assert np.allclose(m.predict_proba(ev), m2.predict_proba(ev))

    if (CFG.raw_tweets_dir.exists() and any(CFG.raw_tweets_dir.iterdir())
            and any((CFG.root / "models").glob(M.MODEL_GLOB))):
        pred = M.Predictor.from_repo()
        out = pred.predict("Dogecoin is the people's crypto", posted_at="2021-02-04T08:00:00Z")
        assert set(out["horizon_d"]) == set(pred.models) and out["p_up"].between(0, 1).all()
        assert (out["anchor_date"] == pd.Timestamp("2021-02-03")).all()  # before 12:00 UTC -> previous close
        last_close = pred.prep.prices.index.max()
        try:
            pred.predict("Doge", posted_at=last_close + pd.Timedelta(days=5))
        except ValueError as e:
            assert "No DOGE close" in str(e)
        else:
            raise AssertionError("expected a ValueError for a post after the last price")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
