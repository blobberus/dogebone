# Findings (auto-drafted by the notebook)

_Generated 2026-10-20 08:30 UTC from 105 posts by 1 accounts, 2021-01-01 to 2021-12-31. Focus horizon: 1 day(s). Edit the wording before presenting, but keep the numbers in sync with the notebook._

## Headline (use this as the slide-3 title)

- On the full window (Jan–Dec 2021; the hand-crafted lexicon has no parameters fit to this data), daily post-sentiment calls got the next-1-day DOGE direction right **53%** of the time vs. **48%** no-skill (+4.8 pp, p = 0.437, n = 17 days): **not** distinguishable from chance.
- Split view, the Jan 2021–Aug 2021 calibration period: 57% vs. 50% no-skill (n = 14 days; too few to conclude).
- Split view, out-of-sample Sep–Dec 2021 data: 33% vs. 33% no-skill (n = 3 days; too few to conclude).

## Supporting findings (pick 2 for the slides)

- **Coverage:** only 19 of 105 posts (18%) contained a sentiment keyword, so only 17 of 69 post days got a call. Most DOGE posts here are terse (a bare 'Doge', an emoji, a meme).
- **Attention vs. words:** regardless of wording, DOGE rose over the next 1d after **54%** of post days vs. **48%** of all days (mean +4.09% vs. +2.15%; n = 69 days, p = 0.192, not significant).
- **Momentum check:** sentiment beat a simple 'yesterday's direction continues' rule (53% vs. 41%). If it didn't, posts are mostly *echoing* price, not leading it.
- **Magnitude:** after bullish calls DOGE averaged +7.11% over 1d; after bearish calls -4.19% (spread +11.3 pp).
- **Horizon decay:** hit rate by horizon (full window): 1d 53%, 3d 53%, 7d 56%.
- **Conviction:** high-conviction days hit 60% (n=5) vs. low-conviction 33% (n=6), so too few days per bucket to judge conviction.
- **Hand-crafted vs. learned keywords (test):** 33% (n=3) vs. 0% (n=1). Learned keywords were fit on Jan 2021–Aug 2021 calibration period only.
- **Keywords that preceded up-moves:** `🤣 🤣`, `doge`, `🤣`, `moon`, `much`. **Down-moves:** `dogecoin`. (Training period, at least 5 posts per term; exploratory.)

## Caveats to say out loud (pick 1)

- Daily prices can't isolate a post's minutes-scale impact; we anchor to the nearest daily close (at most 12h of overlap).
- Overlapping multi-day windows and same-day posts inflate significance; daily aggregation reduces but doesn't remove this.
- Lexicons miss sarcasm and memes (a large share of DOGE posts). Direction only, not price targets.

## Figures exported for slides

- `presentation/figures/01_timeline.png`
- `presentation/figures/02_hit_rate_by_conviction.png`
- `presentation/figures/03_event_study.png`
- `presentation/figures/05_signal_vs_buy_and_hold.png`
- `presentation/figures/04_keywords.png`
