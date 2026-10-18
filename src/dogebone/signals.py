"""Turn scored posts into calls: direction (UP / DOWN / NEUTRAL) + conviction (LOW / MEDIUM / HIGH)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Config

CONVICTION_LEVELS = ["LOW", "MEDIUM", "HIGH"]


def account_weights(posts: pd.DataFrame, accounts: pd.DataFrame, cfg: Config) -> pd.Series:
    w = posts["username"].map(dict(zip(accounts["handle"], accounts["influence_weight"])))
    w = w.fillna(cfg.default_account_weight).astype(float)
    return (w / accounts["influence_weight"].max()) ** cfg.account_weight_power


def direction(score: pd.Series, threshold: float) -> pd.Series:
    return pd.Series(np.select([score >= threshold, score <= -threshold], ["UP", "DOWN"], "NEUTRAL"), index=score.index)


def fit_conviction_cutoffs(conviction: pd.Series, is_call: pd.Series) -> tuple[float, float]:
    """Tercile cutoffs among directional calls. Fit on the training window only."""
    vals = conviction[is_call]
    if len(vals) < 3:
        return (np.inf, np.inf)
    return tuple(vals.quantile([1 / 3, 2 / 3]).to_list())


def conviction_bucket(conviction: pd.Series, is_call: pd.Series, cutoffs: tuple[float, float]) -> pd.Series:
    lo, hi = cutoffs
    b = pd.Series(np.select([conviction >= hi, conviction >= lo], ["HIGH", "MEDIUM"], "LOW"), index=conviction.index)
    return b.where(is_call, "NONE")


def build_post_signals(scored: pd.DataFrame, accounts: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    df = scored.copy()
    df["account_w"] = account_weights(df, accounts, cfg)
    df["context_w"] = df["context"].map(cfg.context_weights).fillna(0.5)
    df["direction"] = direction(df["sentiment"], cfg.neutral_threshold)
    df["conviction"] = df["sentiment"].abs() * df["account_w"] * df["context_w"]
    return df


def build_daily_signals(posts: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Aggregate every post sharing an anchor date into one call (daily prices -> one outcome per day)."""
    p = posts.assign(w=posts["account_w"] * posts["context_w"])
    p = p.assign(ws=p["w"] * p["sentiment"])
    g = p.groupby("anchor_date")
    daily = pd.DataFrame(
        {
            "n_posts": g.size(),
            "n_accounts": g["username"].nunique(),
            "net_weighted_sentiment": g["ws"].sum(),
            "accounts": g["username"].agg(lambda s: ", ".join(sorted(set(s)))),
        }
    )
    daily["score"] = np.tanh(daily["net_weighted_sentiment"])
    daily["direction"] = direction(daily["score"], cfg.neutral_threshold)
    daily["conviction"] = daily["score"].abs()
    return daily.reset_index()


def split_period(df: pd.DataFrame, date_col: str, cfg: Config) -> pd.Series:
    return pd.Series(np.where(df[date_col] <= pd.Timestamp(cfg.train_end), "train", "test"), index=df.index)
