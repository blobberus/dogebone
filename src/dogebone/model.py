"""A trained up/down model: will DOGE close higher h days after a day on which Musk posted about DOGE?

- **Unit:** one row per *post day*, meaning all of the account's DOGE posts that share an anchor close (see `market.anchor_dates`).
- **Target:** `y_{h}d` = 1 if DOGE closed higher h days after the anchor close, 0 if lower. Exactly flat days are dropped.
- **Features:** everything is known at the anchor close (or at post time, whichever is later); nothing after.
  - *Text:* lexicon sentiment, whether any sentiment word was used, number of posts, saying "Doge" outright vs.
    only tagging a DOGE account, original post vs. reply, and days since the previous DOGE post day.
  - *Market:* trailing 1- and 7-day return, 7-day volatility, and distance below the 30-day high.
- **Excluded:** engagement counts (likes, reposts), which accumulate after the post and partly reflect the price reaction.
- **Model:** L2-regularized logistic regression (Newton's method in numpy; no scikit-learn needed).
  Standardization is fit on the training rows only, and missing values are imputed with the training mean.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import market, pipeline
from .config import Config
from .evaluate import binom_sf

TEXT_FEATURES = ["lex_score", "lex_any", "n_posts_log", "text_share", "has_original", "gap_days_log"]
MARKET_FEATURES = ["mom_1d", "mom_7d", "vol_7d", "dd_30d"]
ALL_FEATURES = TEXT_FEATURES + MARKET_FEATURES
FEATURE_SETS = {"text + market": ALL_FEATURES, "text only": TEXT_FEATURES, "market only": MARKET_FEATURES}
FEATURE_LABELS = {
    "lex_score": "Lexicon sentiment of the day's posts",
    "lex_any": "Used any sentiment word",
    "n_posts_log": "Number of DOGE posts that day",
    "text_share": "Share of posts saying 'Doge' outright",
    "has_original": "Has an original post (not only replies)",
    "gap_days_log": "Days since the previous DOGE post day",
    "mom_1d": "DOGE return, last 1 day",
    "mom_7d": "DOGE return, last 7 days",
    "vol_7d": "DOGE volatility, last 7 days",
    "dd_30d": "Distance below the 30-day high",
}
DEFAULT_L2 = 5.0  # fixed a priori (strong shrinkage for ~50 training days); never tuned on the test months
CONVICTION_EDGES = (0.2, 0.4)  # on |2p - 1|: LOW = 40-60% P(up), MEDIUM = 60-70% (or 30-40%), HIGH = 70%+ (or 30%-)
GAP_CAP_DAYS = 30
MODEL_GLOB = "musk_doge_direction_*d.json"


# --- Features -----------------------------------------------------------------------------------------------


def market_features(close: pd.Series, horizons=(1, 3, 7)) -> pd.DataFrame:
    """Per-date forward returns (outcomes) and trailing features (known at that close)."""
    out = market.forward_returns(close.to_frame("close"), sorted(set(horizons) | {1, 7}))
    out["vol_7d"] = np.log(close).diff().rolling(7, min_periods=5).std()
    out["dd_30d"] = close / close.rolling(30, min_periods=10).max() - 1
    return out


def build_event_features(posts: pd.DataFrame, close: pd.Series, horizons=(1, 3, 7), username: str | None = "elonmusk",
                         prior_post_days=None) -> pd.DataFrame:
    """One row per post day: model features, the posts' text, and the outcomes `fwd_ret_{h}d` / `y_{h}d`.

    `posts` is the output of `pipeline.score_posts`. `prior_post_days` are earlier post days that aren't in `posts`
    (e.g. the training history when scoring a new post), used only for the days-since-last-post feature.
    """
    p = posts if username is None else posts[posts["username"] == username]
    if p.empty:
        raise ValueError(f"No posts for username={username!r}")
    key = p["anchor_date"]
    g = p.groupby(key)
    ev = pd.DataFrame(
        {
            "n_posts": g.size(),
            "lex_score": np.tanh((p["account_w"] * p["context_w"] * p["sentiment"]).groupby(key).sum()),
            "lex_any": (p["n_hits"] > 0).groupby(key).max().astype(float),
            "text_share": p["relevance"].eq("text").groupby(key).mean(),
            "has_original": p["message_type"].eq("update").groupby(key).max().astype(float),
            "first_post_at": g["created_at"].min(),
            "matched_terms": g["matched_terms"].agg(lambda s: ", ".join(t for t in s if t)),
            "texts": g["text"].agg(" | ".join),
        }
    )
    ev.index.name = "anchor_date"
    ev["n_posts_log"] = np.log1p(ev["n_posts"])
    prior = pd.DatetimeIndex([] if prior_post_days is None else pd.to_datetime(list(prior_post_days)))
    days = pd.DatetimeIndex(sorted(set(ev.index) | set(prior)))
    prev = pd.Series(days, index=days).shift(1).reindex(ev.index)
    gap = (ev.index.to_series() - prev).dt.days
    ev["gap_days_log"] = np.log1p(gap.fillna(GAP_CAP_DAYS).clip(upper=GAP_CAP_DAYS))
    ev = ev.join(market_features(close, horizons), how="left")
    for h in horizons:
        r = ev[f"fwd_ret_{h}d"]
        ev[f"y_{h}d"] = np.where(r > 0, 1.0, np.where(r < 0, 0.0, np.nan))
    return ev.reset_index()


# --- Model --------------------------------------------------------------------------------------------------


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def _fmt_value(feature: str, v) -> str:
    if pd.isna(v):
        return "n/a"
    if feature.startswith("mom_") or feature == "dd_30d":
        return f"{v:+.1%}"
    if feature == "vol_7d":
        return f"{v:.1%}/day"
    if feature in ("lex_any", "has_original"):
        return "yes" if v >= 0.5 else "no"
    if feature == "n_posts_log":
        return f"{round(math.expm1(v))}"
    if feature == "gap_days_log":
        d = round(math.expm1(v))
        return f"{d}+" if d >= GAP_CAP_DAYS else f"{d}"
    if feature == "text_share":
        return f"{v:.0%}"
    return f"{v:+.2f}"


@dataclass
class DirectionModel:
    """P(DOGE up over the next `horizon` days | post-day features). Fit with `.fit(events)`, score with `.predict(events)`."""

    horizon: int = 1
    features: list = field(default_factory=lambda: list(ALL_FEATURES))
    l2: float = DEFAULT_L2
    coef_: np.ndarray | None = None
    intercept_: float = 0.0
    mean_: np.ndarray | None = None
    scale_: np.ndarray | None = None
    base_rate_: float = float("nan")
    n_train_: int = 0
    train_start_: str | None = None
    train_end_: str | None = None
    meta: dict = field(default_factory=dict)

    @property
    def target(self) -> str:
        return f"y_{self.horizon}d"

    def _design(self, df: pd.DataFrame) -> np.ndarray:
        z = (df[self.features].to_numpy(dtype=float) - self.mean_) / self.scale_
        return np.where(np.isfinite(z), z, 0.0)  # missing -> training mean

    def fit(self, events: pd.DataFrame) -> "DirectionModel":
        d = events[events[self.target].notna()]
        y = d[self.target].to_numpy(dtype=float)
        if len(y) < 2 or y.min() == y.max():
            raise ValueError("Need both up and down outcomes to fit.")
        x = d[self.features].to_numpy(dtype=float)
        self.mean_ = np.nanmean(x, axis=0)
        sd = np.nanstd(x, axis=0)
        self.scale_ = np.where(sd > 1e-12, sd, 1.0)
        a = np.column_stack([np.ones(len(y)), self._design(d)])
        pen = np.full(a.shape[1], float(self.l2))
        pen[0] = 0.0  # the intercept (base rate) is not shrunk
        w = np.zeros(a.shape[1])
        w[0] = math.log(y.mean() / (1 - y.mean()))
        for _ in range(100):  # Newton / IRLS on the penalized log-likelihood
            p = _sigmoid(a @ w)
            grad = a.T @ (p - y) + pen * w
            hess = (a * (p * (1 - p))[:, None]).T @ a + np.diag(pen) + 1e-9 * np.eye(a.shape[1])
            step = np.linalg.solve(hess, grad)
            w -= step
            if np.abs(step).max() < 1e-10:
                break
        self.intercept_, self.coef_ = float(w[0]), w[1:]
        self.base_rate_, self.n_train_ = float(y.mean()), int(len(y))
        self.train_start_, self.train_end_ = f"{d['anchor_date'].min():%Y-%m-%d}", f"{d['anchor_date'].max():%Y-%m-%d}"
        return self

    def predict_proba(self, events: pd.DataFrame) -> np.ndarray:
        if self.coef_ is None:
            raise RuntimeError("Model is not fitted.")
        return _sigmoid(self.intercept_ + self._design(events) @ self.coef_)

    def predict(self, events: pd.DataFrame) -> pd.DataFrame:
        """p_up, direction (UP if p_up >= 0.5), conviction = |2 p_up - 1| and its LOW / MEDIUM / HIGH bucket."""
        p = self.predict_proba(events)
        conv = np.abs(2 * p - 1)
        lo, hi = CONVICTION_EDGES
        return pd.DataFrame(
            {
                "p_up": p,
                "direction": np.where(p >= 0.5, "UP", "DOWN"),
                "conviction": conv,
                "conviction_bucket": np.select([conv >= hi, conv >= lo], ["HIGH", "MEDIUM"], "LOW"),
            },
            index=events.index,
        )

    def contributions(self, events: pd.DataFrame) -> pd.DataFrame:
        """Each feature's push on the log-odds of UP (standardized value x coefficient), per row."""
        return pd.DataFrame(self._design(events) * self.coef_, columns=self.features, index=events.index)

    def reasons(self, events: pd.DataFrame, k: int = 3) -> pd.Series:
        """Plain-English top-k drivers per row, e.g. 'DOGE return, last 7 days = +35.2% (pushes DOWN)'."""
        contrib = self.contributions(events)
        out = {}
        for i, row in contrib.iterrows():
            top = row.abs().sort_values(ascending=False).index[:k]
            out[i] = "; ".join(
                f"{FEATURE_LABELS.get(f, f)} = {_fmt_value(f, events.at[i, f])} (pushes {'UP' if row[f] > 0 else 'DOWN'})"
                for f in top
            )
        return pd.Series(out)

    def coefficients(self) -> pd.DataFrame:
        return (
            pd.DataFrame({"feature": self.features, "label": [FEATURE_LABELS.get(f, f) for f in self.features],
                          "coef_per_sd": self.coef_, "odds_ratio_per_sd": np.exp(self.coef_),
                          "train_mean": self.mean_, "train_sd": self.scale_})
            .assign(abs_=lambda t: t["coef_per_sd"].abs())
            .sort_values("abs_", ascending=False)
            .drop(columns="abs_")
            .reset_index(drop=True)
        )

    # --- persistence ---
    def to_dict(self) -> dict:
        return {
            "model": "L2 logistic regression on Musk DOGE post days",
            "horizon_days": self.horizon, "features": list(self.features),
            "feature_labels": {f: FEATURE_LABELS.get(f, f) for f in self.features}, "l2": self.l2,
            "intercept": self.intercept_, "coef_per_sd": [float(c) for c in self.coef_],
            "train_mean": [float(v) for v in self.mean_], "train_sd": [float(v) for v in self.scale_],
            "base_rate_up": self.base_rate_, "n_train_days": self.n_train_,
            "train_start": self.train_start_, "train_end": self.train_end_,
            "conviction_edges": list(CONVICTION_EDGES), "meta": self.meta,
        }

    def save(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        meta = {"saved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), **self.meta}
        path.write_text(json.dumps({**self.to_dict(), "meta": meta}, indent=2, default=float), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path) -> "DirectionModel":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            horizon=int(d["horizon_days"]), features=list(d["features"]), l2=float(d["l2"]),
            coef_=np.array(d["coef_per_sd"], dtype=float), intercept_=float(d["intercept"]),
            mean_=np.array(d["train_mean"], dtype=float), scale_=np.array(d["train_sd"], dtype=float),
            base_rate_=float(d["base_rate_up"]), n_train_=int(d["n_train_days"]),
            train_start_=d.get("train_start"), train_end_=d.get("train_end"), meta=d.get("meta", {}),
        )


# --- Out-of-sample testing ----------------------------------------------------------------------------------


def _prediction_frame(model: DirectionModel, test: pd.DataFrame, fold: str) -> pd.DataFrame:
    h = model.horizon
    keep = ["anchor_date", "n_posts", "lex_score", "matched_terms", "texts", "close", f"mom_{h}d", f"fwd_ret_{h}d", model.target]
    out = test[[c for c in keep if c in test]].copy().join(model.predict(test))
    y = out[model.target]
    out["actual"] = np.where(y == 1, "UP", np.where(y == 0, "DOWN", None))
    out["hit"] = np.where(y.notna(), out["direction"] == out["actual"], np.nan)
    out["fold"], out["base_rate_train"], out["n_train"] = fold, model.base_rate_, model.n_train_
    return out


def train_mask(events: pd.DataFrame, horizon: int, cutoff) -> pd.Series:
    """Rows whose outcome close (anchor + horizon) is already known before `cutoff`: no overlap with the test period."""
    return events["anchor_date"] + pd.Timedelta(days=horizon) < pd.Timestamp(cutoff)


def holdout(events: pd.DataFrame, horizon: int = 1, train_end: str = "2021-08-31", features=None,
            l2: float = DEFAULT_L2) -> tuple[DirectionModel, pd.DataFrame]:
    """Fit on post days whose outcome is known by `train_end`, predict every later post day once."""
    start = pd.Timestamp(train_end) + pd.Timedelta(days=1)
    model = DirectionModel(horizon, list(features or ALL_FEATURES), l2).fit(events[train_mask(events, horizon, start)])
    return model, _prediction_frame(model, events[events["anchor_date"] >= start], f"holdout from {start:%Y-%m-%d}")


def walk_forward(events: pd.DataFrame, horizon: int = 1, features=None, l2: float = DEFAULT_L2,
                 first_test: str = "2021-03-01", end=None, min_train: int = 15) -> pd.DataFrame:
    """Refit at the start of every month on all earlier post days with known outcomes; predict that month."""
    feats = list(features or ALL_FEATURES)
    end = pd.Timestamp(end) if end is not None else events["anchor_date"].max()
    frames = []
    for m in pd.date_range(pd.Timestamp(first_test), end, freq="MS"):
        test = events[(events["anchor_date"] >= m) & (events["anchor_date"] < m + pd.offsets.MonthBegin(1))]
        train = events[train_mask(events, horizon, m)]
        y = train[f"y_{horizon}d"].dropna()
        if test.empty or len(y) < min_train or y.nunique() < 2:
            continue
        frames.append(_prediction_frame(DirectionModel(horizon, feats, l2).fit(train), test, f"{m:%Y-%m}"))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _auc(y: np.ndarray, p: np.ndarray) -> float:
    n1 = int(y.sum())
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    ranks = pd.Series(p).rank().to_numpy()
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def score_predictions(preds: pd.DataFrame, horizon: int) -> dict:
    """Hit rate vs. honest baselines, plus probability quality (AUC, Brier skill vs. the training base rate)."""
    t = f"y_{horizon}d"
    d = preds[preds[t].notna()] if len(preds) else preds
    n = len(d)
    if n == 0:
        return {"horizon_d": horizon, "n": 0}
    y, p = d[t].to_numpy(dtype=float), d["p_up"].to_numpy(dtype=float)
    up = d["direction"].eq("UP").to_numpy()
    hits = int((up == (y == 1)).sum())
    q, pu = float(up.mean()), float(y.mean())
    null = q * pu + (1 - q) * (1 - pu)  # hit rate if calls were independent of outcomes
    base = d["base_rate_train"].to_numpy(dtype=float)
    brier, brier_ref = float(np.mean((p - y) ** 2)), float(np.mean((base - y) ** 2))
    r = d[f"fwd_ret_{horizon}d"].to_numpy(dtype=float)
    eps = 1e-12
    return {
        "horizon_d": horizon,
        "n": n,
        "hit_rate": hits / n,
        "null_hit_rate": null,
        "edge_pp": (hits / n - null) * 100,
        "p_value": binom_sf(hits, n, null),
        "majority_hit_rate": float(((base >= 0.5) == (y == 1)).mean()),  # always call the training-period majority
        "momentum_hit_rate": float(((d[f"mom_{horizon}d"].to_numpy(dtype=float) > 0) == (y == 1)).mean()),
        "up_rate": pu,
        "share_called_up": q,
        "auc": _auc(y, p),
        "brier": brier,
        "brier_ref": brier_ref,
        "brier_skill": 1 - brier / brier_ref if brier_ref > 0 else float("nan"),
        "log_loss": float(-np.mean(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps))),
        "mean_ret_when_up": float(r[up].mean()) if up.any() else float("nan"),
        "mean_ret_when_down": float(r[~up].mean()) if (~up).any() else float("nan"),
    }


def evaluate_grid(events: pd.DataFrame, horizons, feature_sets: dict | None = None, scheme: str = "walk_forward",
                  train_end: str = "2021-08-31", l2: float = DEFAULT_L2, **wf_kw) -> pd.DataFrame:
    """score_predictions for every (feature set, horizon) under one testing scheme."""
    rows = []
    for name, feats in (feature_sets or FEATURE_SETS).items():
        for h in horizons:
            if scheme == "walk_forward":
                preds = walk_forward(events, h, feats, l2, **wf_kw)
            else:
                preds = holdout(events, h, train_end, feats, l2)[1]
            rows.append({"features": name, **score_predictions(preds, h)})
    return pd.DataFrame(rows)


def by_conviction(preds: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Calibration check: predicted vs. realized up-rate and hit rate per conviction bucket."""
    t = f"y_{horizon}d"
    d = preds[preds[t].notna()]
    g = d.groupby("conviction_bucket", observed=True)
    out = pd.DataFrame({"n": g.size(), "mean_p_up": g["p_up"].mean(), "realized_up_rate": g[t].mean(),
                        "hit_rate": g["hit"].mean()})
    return out.reindex([b for b in ["LOW", "MEDIUM", "HIGH"] if b in out.index]).reset_index()


def permutation_test(events: pd.DataFrame, horizon: int = 1, features=None, l2: float = DEFAULT_L2, n_perm: int = 500,
                     seed: int = 0, shuffle: str = "outcome", **wf_kw) -> dict:
    """Walk-forward skill vs. its distribution when the feature-outcome link is broken.

    shuffle="outcome": permute outcomes across post days. Is *anything* in the features informative?
    shuffle="text":    permute the text-feature block across post days, keeping market features and outcomes.
                       Do Musk's words add anything beyond the market state?
    """
    feats = list(features or ALL_FEATURES)
    obs = score_predictions(walk_forward(events, horizon, feats, l2, **wf_kw), horizon)
    if shuffle == "outcome":
        cols = [f"y_{horizon}d", f"fwd_ret_{horizon}d"]
    elif shuffle == "text":
        cols = [c for c in TEXT_FEATURES if c in feats]
    else:
        raise ValueError("shuffle must be 'outcome' or 'text'")
    rng = np.random.default_rng(seed)
    null = np.empty((n_perm, 3))
    for i in range(n_perm):
        ev = events.copy()
        ev[cols] = ev[cols].to_numpy()[rng.permutation(len(ev))]
        s = score_predictions(walk_forward(ev, horizon, feats, l2, **wf_kw), horizon)
        null[i] = (s["hit_rate"], s["auc"], s["brier_skill"])

    def p_of(j, o):
        return float((1 + np.sum(null[:, j] >= o - 1e-12)) / (n_perm + 1))

    return {
        "horizon_d": horizon, "shuffle": shuffle, "n": obs["n"], "n_perm": n_perm,
        "hit_rate": obs["hit_rate"], "null_hit_rate_mean": float(null[:, 0].mean()), "p_hit_rate": p_of(0, obs["hit_rate"]),
        "auc": obs["auc"], "null_auc_mean": float(np.nanmean(null[:, 1])), "p_auc": p_of(1, obs["auc"]),
        "brier_skill": obs["brier_skill"], "null_brier_skill_mean": float(np.nanmean(null[:, 2])),
        "p_brier_skill": p_of(2, obs["brier_skill"]),
    }


def fit_final(events: pd.DataFrame, horizon: int, features=None, l2: float = DEFAULT_L2, **meta) -> DirectionModel:
    """Fit on every post day with a known outcome. This is the model you deploy, not the one you report skill for."""
    m = DirectionModel(horizon, list(features or ALL_FEATURES), l2).fit(events)
    m.meta.update(meta)
    return m


# --- Scoring new posts --------------------------------------------------------------------------------------


class Predictor:
    """Score new posts with the saved models.

    >>> pred = Predictor.from_repo()
    >>> pred.predict("Dogecoin is the people's crypto", posted_at="2021-12-14T18:00:00Z")
    """

    def __init__(self, models: dict, prepared: pipeline.Prepared, username: str = "elonmusk"):
        self.models = dict(sorted(models.items()))
        self.prep = prepared
        self.username = username

    @classmethod
    def from_repo(cls, model_dir: Path | None = None, cfg: Config | None = None, username: str = "elonmusk") -> "Predictor":
        cfg = cfg or Config()
        model_dir = Path(model_dir or cfg.root / "models")
        models = {m.horizon: m for m in (DirectionModel.load(p) for p in sorted(model_dir.glob(MODEL_GLOB)))}
        if not models:
            raise FileNotFoundError(f"No saved models ({MODEL_GLOB}) in {model_dir}. Run notebooks/02_direction_model.ipynb.")
        return cls(models, pipeline.prepare(cfg), username)

    def features(self, posts, posted_at=None) -> pd.DataFrame:
        """Post-day feature rows for new posts: a string, a list of strings (same timestamp), or a DataFrame with
        `text` and `created_at` columns. Outcome columns are filled in when the prices already cover them."""
        if isinstance(posts, str):
            posts = [posts]
        if not isinstance(posts, pd.DataFrame):
            if posted_at is None:
                raise ValueError("posted_at (UTC time of the post) is required when passing text.")
            posts = pd.DataFrame({"text": list(posts), "created_at": posted_at})
        df = posts.copy()
        df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
        df["username"] = self.username
        p = self.prep
        scored = pipeline.score_posts(df, p.cfg, p.scorer, p.tagger, p.accounts)
        close = p.prices["close"]
        last = scored["anchor_date"].max()
        if last > close.index.max():
            raise ValueError(
                f"No DOGE close for {last:%Y-%m-%d} (prices end {close.index.max():%Y-%m-%d}). "
                "Add newer daily prices to data/raw/prices/ so the market features can be computed."
            )
        hist = p.posts.loc[p.posts["username"] == self.username, "anchor_date"]
        hist = hist[hist < scored["anchor_date"].min()].unique()
        return build_event_features(scored, close, tuple(self.models), self.username, prior_post_days=hist)

    def predict(self, posts, posted_at=None, horizons=None) -> pd.DataFrame:
        """One row per (post day, horizon): P(up), the call, its conviction, and the top three reasons."""
        ev = self.features(posts, posted_at)
        rows = []
        for h, m in self.models.items():
            if horizons and h not in horizons:
                continue
            pr, why = m.predict(ev), m.reasons(ev)
            for i in ev.index:
                y = ev.at[i, f"y_{h}d"]
                rows.append({
                    "anchor_date": ev.at[i, "anchor_date"], "horizon_d": h, "p_up": round(float(pr.at[i, "p_up"]), 3),
                    "direction": pr.at[i, "direction"], "conviction": pr.at[i, "conviction_bucket"],
                    "lexicon_sentiment": round(float(ev.at[i, "lex_score"]), 3), "matched_terms": ev.at[i, "matched_terms"],
                    "top_reasons": why[i],
                    "actual": None if pd.isna(y) else ("UP" if y == 1 else "DOWN"),
                    "actual_return": ev.at[i, f"fwd_ret_{h}d"],
                })
        return pd.DataFrame(rows)
