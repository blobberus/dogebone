"""Align posts to daily closes and compute forward returns without look-ahead."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from .config import Config


def anchor_dates(created_at: pd.Series, cfg: Config, date_only: bool = False) -> pd.Series:
    """Daily close each post is measured *from*.

    Daily candles are UTC, so close[D-1] is the price at 00:00 on day D and close[D] is the price at 24:00.
    """
    ts = created_at.dt.tz_convert("UTC").dt.tz_localize(None)
    day = ts.dt.normalize()
    mode = cfg.date_only_anchor_mode if date_only else cfg.anchor_mode
    if date_only and cfg.anchor_mode != mode:
        warnings.warn(f"Timestamps have no time of day; using anchor_mode='{mode}' instead of '{cfg.anchor_mode}'.")
    if mode == "prev_close":
        return day - pd.Timedelta(days=1)
    if mode == "same_close":
        return day
    if mode == "nearest_close":
        return day.where(ts.dt.hour >= 12, day - pd.Timedelta(days=1))
    raise ValueError(f"Unknown anchor_mode: {mode}")


def forward_returns(prices: pd.DataFrame, horizons, btc: pd.DataFrame | None = None, beta_window: int = 90) -> pd.DataFrame:
    """Per-date table of forward returns, trailing momentum, and (optionally) BTC-adjusted excess returns.

    fwd_ret_h[t] = close[t+h] / close[t] - 1   (known only after t+h: an outcome, never a feature)
    mom_h[t]     = close[t] / close[t-h] - 1   (known at t: a legitimate baseline feature)
    """
    close = prices["close"]
    out = pd.DataFrame(index=prices.index)
    out["close"] = close
    for h in horizons:
        out[f"fwd_ret_{h}d"] = close.shift(-h) / close - 1
        out[f"mom_{h}d"] = close / close.shift(h) - 1
    if btc is not None:
        btc_close = btc["close"].reindex(prices.index).ffill()
        r_d, r_b = close.pct_change(), btc_close.pct_change()
        beta = (r_d.rolling(beta_window).cov(r_b) / r_b.rolling(beta_window).var()).clip(0, 3)
        out["beta_btc"] = beta  # uses returns up to and including t only
        for h in horizons:
            btc_fwd = btc_close.shift(-h) / btc_close - 1
            out[f"xs_ret_{h}d"] = out[f"fwd_ret_{h}d"] - beta * btc_fwd
    return out


def attach_returns(posts: pd.DataFrame, returns: pd.DataFrame, horizons, flat_band: float = 0.0) -> pd.DataFrame:
    df = posts.merge(returns, left_on="anchor_date", right_index=True, how="left")
    for h in horizons:
        r = df[f"fwd_ret_{h}d"]
        df[f"actual_{h}d"] = np.select([r > flat_band, r < -flat_band], ["UP", "DOWN"], default="FLAT")
        df.loc[r.isna(), f"actual_{h}d"] = None
    return df


def event_paths(returns: pd.DataFrame, anchors: pd.Series, groups: pd.Series, pre: int = 5, post: int = 10) -> pd.DataFrame:
    """Average cumulative return path around anchors, per group (classic event-study chart)."""
    close = returns["close"]
    idx = close.index
    rows = []
    for anchor, grp in zip(anchors, groups):
        if anchor not in idx:
            continue
        loc = idx.get_loc(anchor)
        if loc - pre < 0 or loc + post >= len(idx):
            continue
        base = close.iloc[loc]
        path = close.iloc[loc - pre : loc + post + 1].to_numpy() / base - 1
        rows.extend({"group": grp, "day": d, "cum_ret": v} for d, v in zip(range(-pre, post + 1), path))
    if not rows:
        return pd.DataFrame(columns=["group", "day", "mean", "sem", "n"])
    df = pd.DataFrame(rows)
    agg = df.groupby(["group", "day"])["cum_ret"].agg(["mean", "std", "count"]).reset_index()
    agg["sem"] = agg["std"] / np.sqrt(agg["count"])
    return agg.rename(columns={"count": "n"})[["group", "day", "mean", "sem", "n"]]
