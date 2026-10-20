"""Raw files -> scored, anchored posts in one call. Shared by the model notebook, the predictor and the CLI."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import io, market, signals, text
from .config import Config
from .lexicon import LexiconScorer


@dataclass
class Prepared:
    cfg: Config
    data_mode: str  # "raw" or "sample"
    prices: pd.DataFrame
    returns: pd.DataFrame  # market.forward_returns over the full price history
    posts: pd.DataFrame  # one row per post in the analysis window, scored and anchored
    accounts: pd.DataFrame
    events: pd.DataFrame
    scorer: LexiconScorer
    tagger: text.ContextTagger
    date_only: bool


def make_nlp(cfg: Config, accounts: pd.DataFrame) -> tuple[LexiconScorer, text.ContextTagger]:
    default_ctx = dict(zip(accounts["handle"], accounts["default_context"]))
    return LexiconScorer(cfg), text.ContextTagger(cfg.lexicon_dir / "doge_context.csv", default_ctx)


def score_posts(posts: pd.DataFrame, cfg: Config, scorer: LexiconScorer, tagger: text.ContextTagger,
                accounts: pd.DataFrame, date_only: bool = False) -> pd.DataFrame:
    """Context tag + lexicon score + anchor close + per-post call. Needs `text`, `created_at` (UTC), `username`."""
    df = posts.copy()
    if "relevance" not in df:
        df["relevance"] = df["text"].map(text.doge_relevance)
    if "message_type" not in df:
        df["message_type"] = np.where(df["text"].str.lstrip().str.startswith("@"), "reply", "update")
    df["context"] = [tagger.tag(t, u) for t, u in zip(df["text"], df["username"])]
    df = scorer.score_frame(df)
    df["anchor_date"] = market.anchor_dates(df["created_at"], cfg, date_only=date_only)
    return signals.build_post_signals(df, accounts, cfg)


def prepare(cfg: Config) -> Prepared:
    src = io.resolve_sources(cfg)
    prices = io.load_prices(src["doge_price"], cfg)
    posts_all = io.load_tweets(src["tweets"], cfg)
    accounts = io.load_accounts(cfg)
    window = (posts_all["created_at"] >= pd.Timestamp(cfg.analysis_start, tz="UTC")) & (
        posts_all["created_at"] < pd.Timestamp(cfg.analysis_end, tz="UTC") + pd.Timedelta(days=1)
    )
    date_only = posts_all.attrs.get("date_only", False)
    scorer, tagger = make_nlp(cfg, accounts)
    posts = score_posts(posts_all[window].reset_index(drop=True), cfg, scorer, tagger, accounts, date_only)
    return Prepared(
        cfg=cfg, data_mode=src["mode"], prices=prices, returns=market.forward_returns(prices, cfg.horizons),
        posts=posts, accounts=accounts, events=io.load_events(cfg), scorer=scorer, tagger=tagger, date_only=date_only,
    )
