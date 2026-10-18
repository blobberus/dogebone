> ## ⏳ Pending real data
> This file is **overwritten automatically** by the last section of `notebooks/01_doge_post_sentiment_signal.ipynb`.
> Until real files are in `data/raw/`, any numbers here come from synthetic data and must not be presented.

# Findings (auto-drafted by the notebook)

_The notebook fills in every bracket below from the latest run._

## Headline (use this as the slide-3 title)

- On out-of-sample 2022 data, daily post-sentiment calls got the next-1-day DOGE direction right **[hit rate]** of the time vs.
  **[no-skill rate]** no-skill ([edge] pp, p = [p], n = [days]).
- For comparison, the 2021 calibration period: [hit rate] vs. [no-skill rate].

## Supporting findings (pick 2 for the slides)

- **Momentum check:** did sentiment beat a "yesterday's direction continues" rule? If not, posts are mostly *echoing* price, not leading it.
- **Magnitude:** the average DOGE move after bullish vs. bearish calls, and the spread between them.
- **Horizon decay:** hit rate at 1, 3 and 7 days.
- **Conviction:** hit rate of high- vs. low-conviction days.
- **Accounts:** the most and least predictive accounts (n ≥ 30 calls).
- **Hand-crafted vs. learned keywords:** out-of-sample hit rate of each.
- **Keywords** that most often preceded up-moves and down-moves (training period).

## Caveats to say out loud (pick 1)

- Daily prices can't isolate a post's minutes-scale impact; we anchor to the nearest daily close (at most 12h of overlap).
- Overlapping multi-day windows and same-day posts inflate significance; daily aggregation reduces but doesn't remove this.
- Lexicons miss sarcasm and memes (a large share of DOGE posts). Direction only, not price targets.

For background findings from the event research (sourced, usable now), see [`README.md`](README.md#background-findings-you-can-cite-now-sourced-not-from-our-model).
