# Project brief: Dogebone

**Can the words in posts from Dogecoin's most influential X/Twitter accounts call the direction of DOGE's next daily move, and how much should we trust each call?**

| | |
|---|---|
| **Window** | 2021-01-01 to 2021-12-31 (daily UTC closes): calibrate on Jan–Aug, test out-of-sample on Sep–Dec |
| **Inputs** | Every DOGE-related post from the accounts below, plus the DOGE (and optionally BTC) daily price series |
| **Current data** | **@elonmusk only: 105 DOGE-related posts in 2021** (public archive, `scripts/fetch_musk_tweets.py`) and the team's DOGE prices (`scripts/prepare_doge_prices.py`). The other nine accounts are the target list for the next data pull. |
| **Output per post / per day** | **Direction** (UP / DOWN / no call) and **conviction** (LOW / MEDIUM / HIGH), with the matched keywords that explain the call |
| **Horizons** | 1, 3 and 7 days after the post (configurable) |
| **Not in scope** | Price targets, magnitude forecasts, intraday trading, image/video understanding |
| **Format** | 1-hour hackathon powered by Claude Enterprise; 2-minute final presentation |

---

## 1. Why this question and this window

DOGE is the clearest case of a market moved by social media. It has no cash flows, its supply is uncapped, and its 2021 run was openly
driven by posts and memes. 2021 splits into two very different markets:

- **Jan–Aug, the mania and its unwind (calibration set).** The WallStreetBets spillover (Jan), Musk's "people's crypto" posts (Feb), Snoop Dogg and
  Gene Simmons (Feb), the Mavericks accepting DOGE (Mar), the SNL "Dogefather" tease and the "it's a hustle" crash (Apr–May), the Coinbase listing (Jun),
  and the Dogecoin Foundation relaunch (Aug).
- **Sep–Dec, the cooled-off market (out-of-sample test).** The Core 1.14.5 fee cut and Binance's DOGE withdrawal halt (Nov), Bitcoin's cycle top (Nov),
  and Musk's Tesla-merch-in-DOGE announcement (Dec 14).

Tuning on Jan–Aug and testing on Sep–Dec checks whether anything found during the mania survives a calmer market. A signal that only works in a bubble isn't a signal.
`data/reference/key_events.csv` lists 34 dated, sourced events for annotation and sanity checks.

## 2. Hypotheses

| # | Hypothesis | How the notebook tests it |
|---|---|---|
| H1 | Lexicon sentiment predicts next-*h*-day direction better than chance | Daily-call hit rate vs. the **no-skill rate** (the hit rate expected if calls were independent of outcomes), one-sided binomial test |
| H2 | Conviction is calibrated: HIGH-conviction calls hit more often than LOW | Hit rate by conviction tercile (cutoffs fit on Jan–Aug, applied to Sep–Dec) |
| H3 | Posts **lead** price rather than echo it | Sentiment hit rate vs. a momentum baseline; event-study paths before and after day 0 |
| H4 | The effect is short-lived | Hit-rate decay across the 1, 3 and 7-day horizons |
| H5 | Who matters: influence is concentrated | Per-account hit rate and edge; the Musk vs. everyone-else contrast |

## 3. The 10 accounts (target list)

> **Current data covers @elonmusk only** (see the header table). The other nine below are the next accounts to pull.

These were verified for 2021–2022 activity through indexed profiles, dated status URLs, and press coverage. Machine-readable version: [`config/accounts.csv`](config/accounts.csv).
`influence_weight` is a judgment call about how much each account's posts plausibly move price. It scales **conviction**, never direction.

| # | Handle | Who | Category | Weight | Why they're in (2021–2022) |
|---|---|---|---|---|---|
| 1 | [@elonmusk](https://x.com/elonmusk) | Elon Musk | Market mover | 3.0 | Drove most of the window's spikes: the "Dogefather" SNL tease (Apr 28, 2021, +~20%), Tesla merch in DOGE (Jan 2022), and the Twitter takeover (Oct 2022, DOGE roughly doubled). |
| 2 | [@dogecoin](https://x.com/dogecoin) | Dogecoin (official) | Official | 1.0 | The official community voice through the window; boosted the Foundation relaunch in Aug 2021. |
| 3 | [@BillyM2k](https://x.com/BillyM2k) | Billy Markus (co-creator) | Founder / insider | 1.0 | Daily poster, Foundation memes advisor from Aug 2021, and widely covered on supply debates. Mostly jokes, so a hard sentiment test. |
| 4 | [@mcuban](https://x.com/mcuban) | Mark Cuban | Market mover | 1.0 | The Mavericks began accepting DOGE on Mar 4, 2021; his "the one coin people actually use" posts were widely covered. |
| 5 | [@CEOAdam](https://x.com/CEOAdam) | Adam Aron (AMC CEO) | Institutional | 0.8 | A clean adoption series: DOGE poll (Sep 2021), gift cards (Oct 2021), AMC app payments (Apr 2022). |
| 6 | [@MattWallace888](https://x.com/MattWallace888) | Matt Wallace | Community influencer | 0.7 | The loudest DOGE promoter of 2021 (about 430K followers). Faced "Accept Doge" rug-pull accusations in Mar 2022. |
| 7 | [@genesimmons](https://x.com/genesimmons) | Gene Simmons | Celebrity | 0.8 | A burst account: posts cluster Feb 1–9, 2021, around DOGE's then-record high. A small sample, but tied to a major event. |
| 8 | [@DogecoinFdn](https://x.com/DogecoinFdn) | Dogecoin Foundation | Official | 0.7 | Relaunched Aug 2021 with Vitalik Buterin as an adviser; posted the roadmap and staking proposals (Dec 2021). No posts before Aug 2021. |
| 9 | [@dogecoin_devs](https://x.com/dogecoin_devs) | Dogecoin Core developers | Official | 0.7 | Release announcements, e.g. the 1.14.5 fee cut (Nov 2021). Few posts, but each one is tied to an event. |
| 10 | [@whale_alert](https://x.com/whale_alert) | Whale Alert | On-chain tracker | 0.6 | Automated large-transfer alerts; the only systematic on-chain feed verified for the window. |

**Alternates** (swap in if a primary account's data is thin): [@SnoopDogg](https://x.com/SnoopDogg) (celebrity, "Snoop Doge" Feb 2021),
[@JRossNicoll](https://x.com/JRossNicoll) (core developer until Feb 2022), [@DogecoinRise](https://x.com/DogecoinRise) (retail hype account),
[@alicharts](https://x.com/alicharts) (Ali Martinez, analyst; posted as `ali_charts` in 2021–22), [@mishaboar](https://x.com/mishaboar) (low-hype DOGE commentary).

**Considered and excluded:**

- Jackson Palmer (co-creator) made his account private, and his 2021–22 posts aren't retrievable.
- Vitalik Buterin posted about DOGE too rarely.
- DogeDesigner had little reach before 2023.
- Tesla, SpaceX, Coinbase and Robinhood announced their DOGE milestones through Musk, blogs, or press releases. Those milestones are captured as events instead.

### Collection notes for whoever pulls the posts

1. **Pull by numeric user ID, not handle.** Handles change: Ali Martinez was `ali_charts` and is now `alicharts`.
2. Pull **all** posts that mention DOGE or Dogecoin (including bare "Doge" memes), not only opinionated ones. Pre-filtering on sentiment biases the result.
3. Keep timestamps **with time of day** in UTC, and keep emoji and capitalization untouched.
4. Known blind spots:
   - Many Musk DOGE posts are **image-only memes**, and some of his biggest moves came from posts that never say DOGE (Oct 2022, "the bird is freed").
   - Adam Aron usually pairs DOGE with SHIB.
   - Snoop Dogg's "Dogg" collides with "doge" in keyword search.
5. Accepted file formats and column names are in [`data/README.md`](data/README.md). Most scraper exports drop straight in.

## 4. Method

```
posts ──► normalize & tokenize ──► coin-context tag ──► crypto lexicon score ──► direction + conviction ──┐
            (NFKC, URLs, emoji,      (clear $DOGE / coin     (phrases, negation,      (per post, and          │
             elongation)              cues vs. memes)         intensifiers, hedges,     aggregated per day)    ├─► evaluate vs.
                                                              caps, "!")                                       │   baselines
prices ──► daily UTC closes ──► anchor each post to the nearest close ──► forward returns at 1/3/7 days ──────┘
```

- **NLP (`src/dogebone/lexicon.py`, `lexicons/*.csv`).** An explainable keyword model built on VADER's rules (Hutto & Gilbert, 2014) with a
  crypto vocabulary of about 220 terms (*moon*, *hodl*, 🚀, *rug pull*, *withdrawals halted*, *it's a hustle*, …).
  - Greedy longest-phrase matching: *pump and dump* beats *pump*.
  - Negation flips the weight (*not bullish* → bearish).
  - Hedges (*maybe*, *nfa*, a trailing `?`) lower conviction.
  - Every call lists its matched terms, so a result can be explained in one sentence.
- **Data-driven keywords (`evaluate.term_stats`).** Smoothed log-odds of an up-move for every word, bigram, and emoji in **Jan–Aug** posts,
  turned into a learned lexicon and tested on Sep–Dec against the hand-crafted one.
- **No look-ahead (`src/dogebone/market.py`).** Each post is measured from the daily close nearest in time to it, so at most 12h of pre-post movement leaks in.
  Conviction cutoffs and learned keywords are fit on Jan–Aug only. Five lexicon terms inspired by specific 2021 events were removed to avoid hindsight.
- **Honest baselines (`src/dogebone/evaluate.py`).**
  - The no-skill hit rate (not 50%: up-day rates differ between the mania and the rest of the year).
  - A momentum rule (do posts just echo price?).
  - An optional generic-VADER comparison.
  - BTC-adjusted returns when BTC prices are provided.
- **Headline unit = daily call.** Prices are daily, so every post sharing an anchor close is aggregated into one call (influence-weighted).
  Post-level results are reported too, but they share outcomes and overstate significance.

## 5. Deliverables

| Deliverable | Where |
|---|---|
| Runnable analysis | [`notebooks/01_doge_post_sentiment_signal.ipynb`](notebooks/01_doge_post_sentiment_signal.ipynb) |
| Account list and weights | [`config/accounts.csv`](config/accounts.csv) |
| Lexicons (tune without code changes) | [`lexicons/`](lexicons/) |
| Event timeline | [`data/reference/key_events.csv`](data/reference/key_events.csv) |
| Auto-drafted findings and slide charts | [`presentation/findings.md`](presentation/findings.md), `presentation/figures/` |
| 2-minute talk plan and formatting guide | [`presentation/`](presentation/) |

**Definition of done:**

- The notebook runs top to bottom on real data with **no "SYNTHETIC" banner**.
- `presentation/findings.md` is regenerated from that run.
- The 2-minute talk states one headline number, one supporting insight, and one caveat.

## 6. Hackathon run-of-show (60 minutes)

| Time | Who | What |
|---|---|---|
| 0:00–0:10 | Data | Drop price and tweet files into `data/raw/`. Run section 2 of the notebook and fix any column-name or coverage warnings. |
| 0:10–0:30 | NLP | Run the notebook. Read the most bullish and most bearish posts (section 4). Add missing slang to `lexicons/sentiment_lexicon.csv` **using Jan–Aug posts only**, then re-run. |
| 0:10–0:30 | Analyst | Check the evaluation (section 7) against the event timeline: is the edge just a few big event days? Try `anchor_mode="same_close"` as a robustness check. |
| 0:30–0:45 | All | Freeze the lexicon. Final run. Read `presentation/findings.md` and pick the headline and one supporting insight. |
| 0:45–0:60 | Presenter | Build 4–5 slides from `presentation/figures/` following `presentation/formatting_guide.md`. Rehearse to 1:50. |

> **Don't tune the lexicon on Sep–Dec posts.** That leaks the test set into the model, and the out-of-sample number stops meaning anything.

## 7. Risks and caveats

1. **Daily resolution.** A Musk post moves price within minutes, and a daily close blurs that. Reverse causality (posting *because* price moved) is partly controlled by the momentum baseline and event study.
2. **Overlap and dependence.** Multi-day windows overlap and same-day posts share an outcome. Trust the daily-level p-values, not the post-level ones.
3. **Sarcasm, memes, and images.** These are invisible to keywords. Explainability is the trade-off we chose.
4. **Concentration.** A handful of event days (SNL, the Twitter deal) can dominate. Check the results with those days excluded.
5. **Selection.** Ten hand-picked accounts and judgment-call weights. Report per-account results so nothing hides in the average.
