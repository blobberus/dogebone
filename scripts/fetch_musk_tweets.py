"""Build data/raw/tweets/elonmusk_<year>.csv from a public archive of Elon Musk's posts.

    python scripts/fetch_musk_tweets.py --year 2021

Source: Hugging Face dataset `fdaudens/musk-tweets` (a social-listening export of @elonmusk, 2013-2025;
no license stated on the dataset card). It is downloaded once to data/external/ (git-ignored).

Processing:
- keeps only @elonmusk's own X posts (posts, replies, reposts), not other people's mentions of him
- repairs mojibake (UTF-8 that was decoded as Mac Roman, e.g. 'üòÇ' -> '😂')
- takes created_at from the tweet ID itself (exact UTC; verified to match the archive's timestamps)
- keeps posts about DOGE:
    relevance = "text"          the post text (ignoring @handles and URLs) mentions DOGE / Dogecoin / 🐕 / much wow / ...
    relevance = "doge_account"  a reply that only mentions a DOGE account (e.g. '@dogecoin_devs Good progress')
"""

from __future__ import annotations

import argparse
import re
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
URL = "https://huggingface.co/datasets/fdaudens/musk-tweets/resolve/main/elonmusk_data_fixed%20-%20Sheet1.csv"
CACHE = ROOT / "data" / "external" / "fdaudens_musk_tweets.csv"
DOGE_TEXT = re.compile(r"\bdoge|dogecoin|\$doge|🐕|much wow|such wow|\bshibes?\b|Ð", re.IGNORECASE)
DOGE_HANDLE = re.compile(r"@\w*doge\w*", re.IGNORECASE)
TWITTER_EPOCH_MS = 1288834974657


def repair(text: str) -> str:
    try:
        return text.encode("mac_roman").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def main(year: int, cache: Path) -> None:
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading archive (~42 MB) to {cache} ...")
        urllib.request.urlretrieve(URL, cache)
    df = pd.read_csv(cache, low_memory=False)

    df = df[df["SenderScreenName"].astype(str).str.strip().str.lower().eq("elonmusk")]
    df = df[df["MessageType"].isin(["X Update", "X Reply", "X Repost"])]
    df = df[df["Permalink"].astype(str).str.contains(r"/status/\d+", regex=True)].copy()

    ids = df["Permalink"].str.extract(r"/status/(\d+)")[0].astype("int64").to_numpy()
    df["tweet_id"] = ids.astype(str)
    df["created_at"] = pd.to_datetime(np.right_shift(ids, 22) + TWITTER_EPOCH_MS, unit="ms", utc=True)
    df = df[df["created_at"].dt.year == year].drop_duplicates("tweet_id")

    df["text"] = df["Message"].astype(str).map(repair)
    body = df["text"].str.replace(r"https?://\S+|pic\.twitter\.com/\S+", " ", regex=True)
    body = body.str.replace(r"@\w+", " ", regex=True)
    in_text = body.str.contains(DOGE_TEXT)
    to_doge_account = df["text"].str.contains(DOGE_HANDLE)
    df["relevance"] = np.select([in_text, to_doge_account], ["text", "doge_account"], default="")
    total = len(df)
    df = df[df["relevance"] != ""]

    out = pd.DataFrame(
        {
            "tweet_id": df["tweet_id"],
            "created_at": df["created_at"].dt.strftime("%Y-%m-%dT%H:%M:%S.%f").str[:-3] + "Z",
            "username": "elonmusk",
            "text": df["text"],
            "like_count": pd.to_numeric(df["Favorites"], errors="coerce"),
            "retweet_count": pd.to_numeric(df["Retweets"], errors="coerce"),
            "is_retweet": df["MessageType"].eq("X Repost"),
            "message_type": df["MessageType"].str.replace("X ", "", regex=False).str.lower(),
            "relevance": df["relevance"],
            "permalink": df["Permalink"],
        }
    ).sort_values("created_at")
    dst = ROOT / "data" / "raw" / "tweets" / f"elonmusk_{year}.csv"
    out.to_csv(dst, index=False, encoding="utf-8")
    print(f"{year}: {total:,} @elonmusk posts in archive -> {len(out)} DOGE-related written to {dst.relative_to(ROOT)}")
    print(out.groupby(["relevance", "message_type"]).size().to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2021)
    ap.add_argument("--cache", type=Path, default=CACHE)
    args = ap.parse_args()
    main(args.year, args.cache)
