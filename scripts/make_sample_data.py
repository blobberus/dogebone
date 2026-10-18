"""Generate SYNTHETIC prices and posts so the pipeline runs end-to-end before real data lands.

The posts carry a *planted* signal: most opinionated posts lean toward the next day's move 62% of the
time, while "echo" posts just describe the day's move so far. A working pipeline should recover a
1-day hit rate of about 55-60%. If it reports far more, something is leaking future information.

Columns deliberately mimic real exports (Yahoo-style prices, Apify-style tweets) to exercise the loaders.

    python scripts/make_sample_data.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sample"
SEED = 42

BULLISH = [
    "Dogecoin to the moon 🚀🚀",
    "$DOGE breakout incoming, very bullish",
    "Accumulating more DOGE on this dip. HODL 💎🙌",
    "X Payments will accept Dogecoin. Huge for adoption",
    "Dogecoin is the people's crypto. Coinbase listing is huge",
    "Not selling a single Dogecoin. Diamond hands",
    "Much wow. $DOGE golden cross on the daily 📈",
    "Dogecoin rally is just getting started, LFG!!",
    "Such wow. Dogecoin adoption keeps growing 🐕",
    "Whales accumulating $DOGE, new high soon 🔥",
]
BEARISH = [
    "DOGE looks bearish here, lower highs 📉",
    "Careful, $DOGE could dump hard. Taking profit",
    "Dogecoin breakdown below support, crash risk",
    "Huge sell off in memecoins, DOGE tanking",
    "$DOGE death cross. Not bullish at all",
    "Whales dumping Dogecoin 🔴 beware",
    "Binance DOGE withdrawals halted again. Not great",
    "This DOGE pump and dump will end badly 🤡",
]
NEUTRAL = [
    "Dogecoin Core 1.14.5 release notes are out",
    "What's your favorite Dogecoin meme?",
    "Dogecoin community meetup this weekend 🐶",
    "1,000,000,000 #DOGE transferred to an unknown wallet",
    "Dogecoin turns 8 today",
]
MEME = [  # no explicit coin cue -> tagged 'ambiguous' unless the account defaults to coin
    "Doge 🐕",
    "Much wow, such Doge",
    "Who let the Doge out",
]


def make_prices(rng, start="2020-12-15", end="2023-01-15"):
    dates = pd.date_range(start, end, freq="D")
    n = len(dates)
    btc_r = rng.normal(0.0012, 0.028, n)
    doge_r = 1.35 * btc_r + rng.normal(0.0, 0.035, n)
    return dates, btc_r, doge_r


def main():
    rng = np.random.default_rng(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    accounts = pd.read_csv(ROOT / "config" / "accounts.csv")
    accounts = accounts[accounts["tier"] == "primary"].reset_index(drop=True)
    dates, btc_r, doge_r = make_prices(rng)

    posts = []
    in_window = (dates >= "2021-01-01") & (dates <= "2022-12-31")
    rates = (accounts["influence_weight"] / accounts["influence_weight"].max() * 0.35 + 0.05).to_numpy()
    for i in np.where(in_window)[0]:
        fwd = doge_r[i + 1]  # the planted "future" move (the next daily return after the anchor close)
        back = doge_r[i]  # the move already visible when the post goes out
        for (_, acc), rate in zip(accounts.iterrows(), rates):
            for _ in range(rng.poisson(rate)):
                roll = rng.random()
                if acc["default_context"] == "ambiguous" and rng.random() < 0.3:
                    text = rng.choice(MEME)
                elif roll < 0.25:
                    text = rng.choice(NEUTRAL)
                elif roll < 0.40:  # momentum echo: describes yesterday's move
                    text = rng.choice(BULLISH if back > 0 else BEARISH)
                else:  # planted predictive signal, 62% accurate
                    leans_up = (fwd > 0) if rng.random() < 0.62 else (fwd <= 0)
                    text = rng.choice(BULLISH if leans_up else BEARISH)
                hour = int(rng.integers(12, 24))  # after midday UTC so the move lands after the anchor close
                ts = dates[i] + pd.Timedelta(hours=hour, minutes=int(rng.integers(0, 60)))
                posts.append(
                    {
                        "id": f"{len(posts):09d}",
                        "createdAt": ts.strftime("%a %b %d %H:%M:%S +0000 %Y"),  # X / Apify format
                        "text": text,
                        "author.userName": acc["handle"],
                        "likeCount": int(rng.lognormal(6 + 2 * rate, 1.2)),
                        "retweetCount": int(rng.lognormal(4 + 2 * rate, 1.2)),
                    }
                )

    doge_close = 0.0047 * np.exp(np.cumsum(np.log1p(doge_r)))
    btc_close = 29000 * np.exp(np.cumsum(np.log1p(btc_r)))
    for name, close in [("doge", doge_close), ("btc", btc_close)]:
        pd.DataFrame(
            {"Date": dates.strftime("%Y-%m-%d"), "Open": np.r_[close[0], close[:-1]], "Close": close,
             "Adj Close": close, "Volume": rng.integers(10**8, 10**9, len(dates))}
        ).to_csv(OUT / f"{name}_daily_SYNTHETIC.csv", index=False)
    pd.DataFrame(posts).to_csv(OUT / "tweets_SYNTHETIC.csv", index=False)
    print(f"Wrote {len(posts):,} synthetic posts and {len(dates)} days of prices to {OUT}")


if __name__ == "__main__":
    main()
