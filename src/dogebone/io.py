"""Loaders that accept the messy column names real exports use and return canonical frames."""

from __future__ import annotations

import json
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from .config import Config

COLUMN_ALIASES = {
    "prices": {
        "date": ["date", "timestamp", "time", "snapped_at", "timeopen", "datetime", "day"],
        "close": ["close", "adj close", "adj_close", "price", "close_price", "closing_price", "close (usd)"],
        "open": ["open"],
        "high": ["high"],
        "low": ["low"],
        "volume": ["volume", "vol.", "total_volume"],
    },
    "tweets": {
        "created_at": ["created_at", "createdat", "date", "datetime", "timestamp", "time", "tweet_created_at"],
        "text": ["text", "full_text", "fulltext", "rawcontent", "content", "tweet", "tweet_text", "body"],
        "username": [
            "username", "screen_name", "handle", "account", "author.username", "user.username",
            "user.screen_name", "author_username", "author", "user",
        ],
        "tweet_id": ["tweet_id", "id", "id_str", "tweetid"],
        "like_count": ["like_count", "likecount", "favorite_count", "likes", "favorites"],
        "retweet_count": ["retweet_count", "retweetcount", "retweets"],
        "is_retweet": ["is_retweet", "isretweet", "retweeted"],
    },
}


def _rename_with_aliases(df: pd.DataFrame, kind: str) -> pd.DataFrame:
    lower_to_orig = {str(c).strip().lower(): c for c in df.columns}
    rename = {}
    for canonical, aliases in COLUMN_ALIASES[kind].items():
        for alias in aliases:
            if alias in lower_to_orig and lower_to_orig[alias] not in rename:
                rename[lower_to_orig[alias]] = canonical
                break
    return df.rename(columns=rename)


def _to_number(s: pd.Series) -> pd.Series:
    """Parse '0.0891', '1,234.5', '1.2B', '-3.1%' style strings."""
    if pd.api.types.is_numeric_dtype(s):
        return s.astype(float)
    mult = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}
    cleaned = s.astype(str).str.replace(",", "", regex=False).str.replace("$", "", regex=False).str.strip()
    suffix = cleaned.str[-1].str.upper()
    factor = suffix.map(mult).fillna(1.0)
    cleaned = cleaned.where(~suffix.isin(list(mult)), cleaned.str[:-1]).str.rstrip("%")
    return pd.to_numeric(cleaned, errors="coerce") * factor


TWITTER_TS_RE = re.compile(r"^[A-Z][a-z]{2} [A-Z][a-z]{2} \d{2} \d{2}:\d{2}:\d{2} [+-]\d{4} \d{4}$")


def _to_utc(s: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(s):  # unix epoch seconds or milliseconds
        unit = "ms" if s.dropna().abs().median() > 1e11 else "s"
        return pd.to_datetime(s, unit=unit, utc=True)
    first = str(s.dropna().iloc[0]) if s.notna().any() else ""
    if TWITTER_TS_RE.match(first):  # "Fri Nov 24 17:49:36 +0000 2023" (X API v1.1 / Apify)
        return pd.to_datetime(s, utc=True, format="%a %b %d %H:%M:%S %z %Y")
    try:
        return pd.to_datetime(s, utc=True)
    except (ValueError, TypeError):
        return pd.to_datetime(s, utc=True, format="mixed")


def _read_any(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")
    if suffix == ".jsonl":
        with open(path, encoding="utf-8") as f:
            return pd.json_normalize([json.loads(line) for line in f if line.strip()])
    if suffix == ".json":
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict):  # e.g. {"data": [...]} from the X API
            payload = next((v for v in payload.values() if isinstance(v, list)), [payload])
        return pd.json_normalize(payload)
    raise ValueError(f"Unsupported file type: {path}")


def find_files(directory: Path, keyword: str | None = None, exts=(".csv", ".json", ".jsonl")) -> list[Path]:
    if not directory.exists():
        return []
    files = sorted(p for p in directory.iterdir() if p.suffix.lower() in exts and not p.name.startswith("."))
    if keyword:
        files = [p for p in files if keyword in p.name.lower()]
    return files


def resolve_sources(cfg: Config) -> dict:
    """Decide raw vs sample data and return the file paths to load."""
    raw = {
        "doge": find_files(cfg.raw_prices_dir, "doge", exts=(".csv",)),
        "btc": find_files(cfg.raw_prices_dir, "btc", exts=(".csv",)),
        "tweets": find_files(cfg.raw_tweets_dir),
    }
    raw_ready = bool(raw["doge"]) and bool(raw["tweets"])
    if cfg.data_mode == "raw" or (cfg.data_mode == "auto" and raw_ready):
        if not raw_ready:
            raise FileNotFoundError(
                f"data_mode='raw' but missing files. Prices found: {raw['doge']}, tweets found: {raw['tweets']}"
            )
        mode, src = "raw", raw
    else:
        mode = "sample"
        src = {
            "doge": find_files(cfg.sample_dir, "doge", exts=(".csv",)),
            "btc": find_files(cfg.sample_dir, "btc", exts=(".csv",)),
            "tweets": find_files(cfg.sample_dir, "tweets"),
        }
        if not src["doge"] or not src["tweets"]:
            raise FileNotFoundError("No raw data and no sample data. Run: python scripts/make_sample_data.py")
    return {
        "mode": mode,
        "doge_price": src["doge"][0],
        "btc_price": src["btc"][0] if src["btc"] else None,
        "tweets": src["tweets"],
    }


def load_prices(path: Path, cfg: Config) -> pd.DataFrame:
    """Daily close series indexed by tz-naive UTC date, reindexed to a gap-free calendar."""
    df = _rename_with_aliases(_read_any(Path(path)), "prices")
    missing = {"date", "close"} - set(df.columns)
    if missing:
        raise ValueError(f"{path}: missing required columns {missing}. Found: {list(df.columns)}")
    out = pd.DataFrame({"date": _to_utc(df["date"]).dt.tz_localize(None).dt.normalize()})
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            out[col] = _to_number(df[col])
    out = out.dropna(subset=["close"]).drop_duplicates("date", keep="last").set_index("date").sort_index()
    if cfg.price_is_start_of_day_snapshot:
        out.index = out.index - pd.Timedelta(days=1)
    full = pd.date_range(out.index.min(), out.index.max(), freq="D")
    n_gaps = len(full) - len(out)
    if n_gaps:
        warnings.warn(f"{Path(path).name}: {n_gaps} missing calendar days forward-filled.")
    out = out.reindex(full).ffill()
    out.index.name = "date"
    out.attrs["n_filled_gaps"] = n_gaps
    return out


def load_tweets(paths: list[Path], cfg: Config) -> pd.DataFrame:
    frames = []
    for path in paths:
        df = _rename_with_aliases(_read_any(Path(path)), "tweets")
        if "username" not in df.columns:  # one file per account: infer handle from file name
            df["username"] = Path(path).stem
        df["source_file"] = Path(path).name
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    missing = {"created_at", "text"} - set(df.columns)
    if missing:
        raise ValueError(f"Tweet files missing required columns {missing}. Found: {list(df.columns)}")

    df["created_at"] = _to_utc(df["created_at"])
    df["text"] = df["text"].astype(str)
    df["username"] = df["username"].astype(str).str.strip().str.lstrip("@").str.lower()
    if "tweet_id" not in df.columns:
        df["tweet_id"] = np.arange(len(df))
    df["tweet_id"] = df["tweet_id"].astype(str)
    if "is_retweet" in df.columns:
        df["is_retweet"] = df["is_retweet"].astype(str).str.lower().isin(["true", "1", "yes"])
    else:
        df["is_retweet"] = df["text"].str.match(r"^RT @\w+:")
    for col in ["like_count", "retweet_count"]:
        if col in df.columns:
            df[col] = _to_number(df[col])

    n0 = len(df)
    df = df.dropna(subset=["created_at"]).drop_duplicates("tweet_id")
    df = df.drop_duplicates(["username", "created_at", "text"])
    if not cfg.include_retweets:
        df = df[~df["is_retweet"]]
    df = df.sort_values("created_at").reset_index(drop=True)
    df.attrs["n_dropped"] = n0 - len(df)
    df.attrs["date_only"] = bool((df["created_at"].dt.floor("D") == df["created_at"]).all())
    keep = ["tweet_id", "created_at", "username", "text", "like_count", "retweet_count", "is_retweet", "source_file"]
    return df[[c for c in keep if c in df.columns]]


def load_accounts(cfg: Config) -> pd.DataFrame:
    acc = pd.read_csv(cfg.accounts_path)
    acc["handle"] = acc["handle"].str.lstrip("@").str.lower()
    return acc


def load_events(cfg: Config) -> pd.DataFrame:
    if not cfg.events_path.exists():
        return pd.DataFrame(columns=["date", "label", "category", "expected_direction", "description", "source_url"])
    ev = pd.read_csv(cfg.events_path)
    ev["date"] = pd.to_datetime(ev["date"], errors="coerce")
    return ev.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
