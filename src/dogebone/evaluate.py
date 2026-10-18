"""Hit-rate evaluation against honest baselines, plus data-driven keyword discovery."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .config import Config
from .text import content_tokens, ngrams


def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p), computed in log space (no scipy needed)."""
    if n == 0:
        return float("nan")
    p = min(max(p, 1e-12), 1 - 1e-12)
    log_terms = [
        math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * math.log(p) + (n - i) * math.log(1 - p)
        for i in range(k, n + 1)
    ]
    if not log_terms:
        return 0.0
    m = max(log_terms)
    return float(min(1.0, math.exp(m) * sum(math.exp(t - m) for t in log_terms)))


def spearman(a: pd.Series, b: pd.Series) -> float:
    mask = a.notna() & b.notna()
    if mask.sum() < 3 or a[mask].nunique() < 2 or b[mask].nunique() < 2:
        return float("nan")
    return float(a[mask].rank().corr(b[mask].rank()))


def directional_metrics(df: pd.DataFrame, horizon: int, pred_col: str = "direction", score_col: str = "sentiment") -> dict:
    actual, ret, mom = f"actual_{horizon}d", f"fwd_ret_{horizon}d", f"mom_{horizon}d"
    has_outcome = df[actual].isin(["UP", "DOWN"])
    calls = df[has_outcome & df[pred_col].isin(["UP", "DOWN"])]
    n = len(calls)
    hits = int((calls[pred_col] == calls[actual]).sum())
    p_up = (calls[actual] == "UP").mean() if n else np.nan
    q_up = (calls[pred_col] == "UP").mean() if n else np.nan
    null_rate = q_up * p_up + (1 - q_up) * (1 - p_up) if n else np.nan  # hit rate if calls ignored outcomes
    mom_dir = np.sign(calls[mom]) if mom in calls else pd.Series(dtype=float)
    mom_hit = (mom_dir == np.where(calls[actual] == "UP", 1, -1)).mean() if n and mom in calls else np.nan
    up_ret = calls.loc[calls[pred_col] == "UP", ret].mean()
    down_ret = calls.loc[calls[pred_col] == "DOWN", ret].mean()
    return {
        "horizon_d": horizon,
        "n_calls": n,
        "coverage": n / max(int(has_outcome.sum()), 1),
        "hit_rate": hits / n if n else np.nan,
        "null_hit_rate": null_rate,
        "edge_pp": (hits / n - null_rate) * 100 if n else np.nan,
        "p_value": binom_sf(hits, n, null_rate) if n else np.nan,
        "always_up_rate": p_up,
        "momentum_hit_rate": mom_hit,
        "mean_ret_when_up": up_ret,
        "mean_ret_when_down": down_ret,
        "spread_pp": (up_ret - down_ret) * 100 if n else np.nan,
        "ic_spearman": spearman(df.loc[has_outcome, score_col], df.loc[has_outcome, ret]),
    }


def evaluate(df: pd.DataFrame, horizons, by: str | list | None = None, **kw) -> pd.DataFrame:
    rows = []
    groups = [((), df)] if by is None else df.groupby(by, observed=True)
    for key, g in groups:
        key = key if isinstance(key, tuple) else (key,)
        for h in horizons:
            m = directional_metrics(g, h, **kw)
            if by is not None:
                m = {**dict(zip([by] if isinstance(by, str) else by, key)), **m}
            rows.append(m)
    return pd.DataFrame(rows)


def attention_test(returns: pd.DataFrame, post_dates, horizon: int, start, end) -> dict:
    """Is it the words, or just the mention? Compare forward returns after post days with every day in the window."""
    r = returns.loc[start:end, f"fwd_ret_{horizon}d"].dropna()
    on = r[r.index.isin(pd.DatetimeIndex(post_dates))]
    k, n = int((on > 0).sum()), len(on)
    p_all = float((r > 0).mean())
    return {
        "horizon_d": horizon,
        "n_post_days": n,
        "up_rate_post_days": k / n if n else np.nan,
        "up_rate_all_days": p_all,
        "p_value": binom_sf(k, n, p_all) if n else np.nan,
        "mean_ret_post_days": on.mean(),
        "mean_ret_all_days": r.mean(),
    }


def term_stats(df: pd.DataFrame, horizon: int, cfg: Config, text_col: str = "text") -> pd.DataFrame:
    """Which keywords precede UP vs DOWN moves? Smoothed log-odds ratio vs. the base rate, with z-scores."""
    actual, ret = f"actual_{horizon}d", f"fwd_ret_{horizon}d"
    d = df[df[actual].isin(["UP", "DOWN"])]
    terms = d[text_col].map(lambda t: sorted(ngrams(content_tokens(t), 2)))
    long = pd.DataFrame({"term": terms, "up": d[actual].eq("UP").astype(int), "ret": d[ret]}).explode("term").dropna()
    if long.empty:
        return pd.DataFrame(columns=["term", "n", "n_up", "n_down", "up_rate", "mean_ret", "log_odds", "z"])
    stats = long.groupby("term").agg(n=("up", "size"), n_up=("up", "sum"), mean_ret=("ret", "mean"))
    stats = stats[stats["n"] >= cfg.min_term_count].copy()
    stats["n_down"] = stats["n"] - stats["n_up"]
    a = cfg.smoothing
    n_up_all, n_down_all = int(d[actual].eq("UP").sum()), int(d[actual].eq("DOWN").sum())
    base = math.log((n_up_all + a) / (n_down_all + a))
    stats["up_rate"] = stats["n_up"] / stats["n"]
    stats["log_odds"] = np.log((stats["n_up"] + a) / (stats["n_down"] + a)) - base
    stats["z"] = stats["log_odds"] / np.sqrt(1 / (stats["n_up"] + a) + 1 / (stats["n_down"] + a))
    return stats.reset_index().sort_values("z", ascending=False)[
        ["term", "n", "n_up", "n_down", "up_rate", "mean_ret", "log_odds", "z"]
    ]


def learned_lexicon(stats: pd.DataFrame, z_min: float) -> dict:
    keep = stats[stats["z"].abs() >= z_min]
    return dict(zip(keep["term"], keep["log_odds"]))


def score_learned(texts: pd.Series, weights: dict) -> pd.Series:
    def _score(t):
        present = ngrams(content_tokens(t), 2)
        return float(np.tanh(sum(weights.get(g, 0.0) for g in present)))

    return texts.map(_score)


def signal_equity(returns: pd.DataFrame, daily: pd.DataFrame, start, end) -> pd.DataFrame:
    """Illustrative only: follow the daily call for 1 day (long UP, short DOWN, flat otherwise), no costs."""
    r = returns.loc[start:end, "fwd_ret_1d"].dropna()
    pos = daily.set_index("anchor_date")["direction"].map({"UP": 1, "DOWN": -1}).reindex(r.index).fillna(0)
    return pd.DataFrame(
        {"buy_and_hold": (1 + r).cumprod(), "follow_signal": (1 + pos * r).cumprod(), "position": pos}
    )
