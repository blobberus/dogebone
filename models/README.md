# Musk → DOGE direction model

**What it does:** on a day Elon Musk posts about DOGE, it estimates **P(DOGE closes higher h days later)** for h = 1, 3 and 7 days.
From that it makes a **call** (UP / DOWN) with a **conviction** (LOW / MEDIUM / HIGH) and lists the **three features that drove it**.
It forecasts direction only, never a price target.

> **Read this first.** Tested out-of-sample on 2021, the model is **not reliably better than chance** at the pre-registered 1-day horizon.
> The 3-day horizon shows a lead that doesn't survive a correction for testing three horizons. See [Results](#results).
> Treat the output as a structured, explainable reading of a post, not a trading signal.

| File | What it is |
|---|---|
| `musk_doge_direction_1d.json`, `_3d.json`, `_7d.json` | One fitted model per horizon: coefficients, training means and SDs, base rate, and the out-of-sample test metrics (`meta`) |
| [`../src/dogebone/model.py`](../src/dogebone/model.py) | The code: features, model, tests, `Predictor` |
| [`../notebooks/02_direction_model.ipynb`](../notebooks/02_direction_model.ipynb) | Trains, tests and re-exports these files |
| [`../scripts/predict.py`](../scripts/predict.py) | Command-line wrapper |
| [`../presentation/model_findings.md`](../presentation/model_findings.md) | Full results, auto-drafted by the notebook |

## Quick use

**Command line**

```bash
python scripts/predict.py "Dogecoin is the people's crypto" --at 2021-02-04T08:00:00Z
python scripts/predict.py "Doge to the moon" "Much wow" --at 2021-05-08T20:00:00Z --horizon 1 3   # two posts, same day
```

```
1d after the 2021-02-03 close: UP, P(up) = 94%, conviction HIGH  | actual: UP (+41.8%)
    why: DOGE return, last 7 days = +403.6% (pushes UP); DOGE volatility, last 7 days = 65.1%/day (pushes UP); ...
```

**Python**

```python
import sys; sys.path.insert(0, "src")
from dogebone.model import Predictor

pred = Predictor.from_repo()          # loads models/*.json, the DOGE prices and the lexicon
pred.predict("Tesla will make some merch buyable with Doge & see how it goes", posted_at="2021-12-14T10:00:00Z")
```

| anchor_date | horizon_d | p_up | direction | conviction | lexicon_sentiment | actual | actual_return |
|---|---|---|---|---|---|---|---|
| 2021-12-13 | 1 | 0.642 | UP | MEDIUM | 0.0 | UP | +21.4% |
| 2021-12-13 | 3 | 0.585 | UP | LOW | 0.0 | UP | +10.0% |
| 2021-12-13 | 7 | 0.503 | UP | LOW | 0.0 | UP | +6.2% |

`top_reasons` (1d): *Has an original post (not only replies) = yes (pushes UP); Share of posts saying 'Doge' outright = 100% (pushes UP);
Number of DOGE posts that day = 1 (pushes UP)*. The post went out at 10:34 UTC, before noon, so it is measured from the Dec 13 close.

> The 2021 examples above are **in-sample** for the shipped models, which were fit on all of 2021. For an honest demo,
> section 9 of the notebook scores Musk's last 2021 posts with the Jan–Aug model, which never saw them.

## `Predictor`: the function reference

### `Predictor.from_repo(model_dir=None, cfg=None, username="elonmusk")`

Loads every `musk_doge_direction_*d.json` in `model_dir` (default `models/`), and the repo's prices, posts, lexicon and accounts through `pipeline.prepare(cfg)`.

### `Predictor.predict(posts, posted_at=None, horizons=None) -> pandas.DataFrame`

| Argument | Type | Meaning |
|---|---|---|
| `posts` | `str`, `list[str]`, or `DataFrame` | One post, several posts at the same time, or a frame with `text` and `created_at` columns (any number of days) |
| `posted_at` | timestamp or ISO string | **UTC** time of the post(s). Required unless `posts` is a DataFrame. |
| `horizons` | `list[int]` or `None` | Subset of the saved horizons (default: all) |

It returns one row per **(post day, horizon)**:

| Column | Meaning |
|---|---|
| `anchor_date` | The daily close the forecast is measured *from*. Posts before 12:00 UTC anchor to the previous day's close, later posts to the same day's close. |
| `horizon_d` | Days ahead |
| `p_up` | Model probability that DOGE closes higher at `anchor_date + horizon_d` |
| `direction` | `UP` if `p_up` ≥ 0.5, else `DOWN` |
| `conviction` | `LOW` (P(up) 40–60%), `MEDIUM` (60–70% or 30–40%), `HIGH` (≥ 70% or ≤ 30%) |
| `lexicon_sentiment` | The hand-built lexicon's daily score (−1 to +1), one of the inputs |
| `matched_terms` | Lexicon terms found in the post(s), with their weights |
| `top_reasons` | The three features with the largest push on the log-odds, in plain English |
| `actual`, `actual_return` | What DOGE did, if the repo's prices already cover the horizon; otherwise `None` / NaN |

**Requirements, errors and warnings**

| Situation | What happens |
|---|---|
| Anchor close after the last price in `data/raw/prices/` | `ValueError: No DOGE close for <date> (prices end ...)`. To score a post from today, add up-to-date daily prices first. |
| Anchor before the first price, or fewer than ~10 closes before it | `ValueError`. The market features would be missing, and the model never fills them in silently. |
| `posted_at` is a bare date such as `"2021-12-14"` | Warning. It anchors to that day's close (`date_only_anchor_mode`), not to the previous close as 00:00 UTC would. Pass a full UTC time for the exact anchor. |
| The post neither mentions DOGE nor tags a DOGE account | Warning. The model was trained on DOGE posts only, so the call is out of scope. |
| No `message_type` column | A post starting with "@" counts as a reply. Pass `message_type` (`update` / `reply`) to match the training export exactly; in 2021, 4 of 82 replies didn't start with "@". |

"Days since the previous DOGE post" uses the posts in `data/raw/tweets/` dated before each new post day, plus the other days in the
same batch. For dates after the newest post on file (2021-12-22), it can't see posts it was never given and caps the gap at 30 days.

### `Predictor.features(posts, posted_at=None) -> pandas.DataFrame`

Same inputs. Returns the feature row(s) the models see, which is useful for debugging a surprising call.

## Lower-level API (`dogebone.model`)

| Function / class | What it does |
|---|---|
| `build_event_features(posts, close, horizons, username, prior_post_days)` | Scored posts (`pipeline.score_posts`) → one row per post day: features, the posts' text, `fwd_ret_{h}d` and `y_{h}d` |
| `DirectionModel(horizon, features, l2)` | `.fit(events)`, `.predict_proba`, `.predict` (p_up, direction, conviction), `.contributions` (per-feature log-odds push), `.reasons`, `.coefficients()`, `.save(path)` / `DirectionModel.load(path)` |
| `holdout(events, h, train_end)` | Fit on post days whose outcome is known by `train_end`; predict every later post day once |
| `walk_forward(events, h, first_test=...)` | Refit at each month start on earlier post days with known outcomes; predict that month |
| `score_predictions(preds, h)` | Hit rate, no-skill rate, binomial p, majority and momentum baselines, AUC, Brier skill, log loss |
| `evaluate_grid(events, horizons, scheme=...)` | `score_predictions` for every feature set (text + market, text only, market only) × horizon |
| `by_conviction(preds, h)` | Predicted vs. realized up-rate and hit rate per conviction bucket |
| `permutation_test(events, h, shuffle="outcome" or "text")` | Walk-forward skill vs. shuffled outcomes, or vs. shuffled text features with the market kept |
| `fit_final(events, h)` | The deployable model, fit on every post day with a known outcome |

## How the model works

**Unit.** All of Musk's DOGE posts that share an anchor close form one **post day**, because prices are daily. 2021 has 105 posts on 69 post days.

**Features.** Each is known at the anchor close or at post time, whichever is later.

| Feature | Group | Meaning |
|---|---|---|
| `lex_score` | text | Lexicon sentiment of the day's posts (−1 to +1) |
| `lex_any` | text | Any sentiment word used (0/1). Only about a quarter of post days have one. |
| `n_posts_log` | text | log(1 + number of DOGE posts that day) |
| `text_share` | text | Share of posts saying "Doge" outright, vs. replies that only tag a DOGE account |
| `has_original` | text | At least one original post (shown to all followers), not only replies (0/1) |
| `gap_days_log` | text | log(1 + days since the previous DOGE post day), capped at 30 |
| `mom_1d`, `mom_7d` | market | DOGE return over the 1 and 7 days into the anchor close |
| `vol_7d` | market | Standard deviation of daily log returns, last 7 days |
| `dd_30d` | market | Distance below the 30-day high |

Likes and reposts are excluded: they keep accumulating after the post and partly reflect the price reaction.

**Model.** L2-regularized logistic regression, solved by Newton's method in numpy (no scikit-learn needed).

- Features are standardized with the **training** mean and SD, so each coefficient is the log-odds push per 1 SD. Missing values become the training mean.
- The penalty (`l2 = 5`) shrinks every coefficient toward the base rate. The intercept isn't penalized.

**Fixed before testing:**

- the feature list;
- `l2 = 5`;
- the horizons (1, 3, 7);
- the focus horizon (1 day);
- the conviction cut-offs.

Nothing was tuned on test months.

**Testing.**

| Test | Train | Predict |
|---|---|---|
| Held-out (pre-registered) | 2021 post days whose outcome close (anchor + h) falls on or before Aug 31 | Every Sep–Dec 2021 post day, once |
| Walk-forward | At each month start, every earlier post day whose outcome is already known (purged, so no window straddles the boundary) | That month, Mar–Dec 2021 |

Baselines are scored on the same days:

- the **no-skill rate**: the hit rate expected if calls ignored outcomes, given the UP/DOWN mix;
- **always calling the training majority**;
- **momentum** (the last *h* days' direction continues);
- the **training base rate** as a probability forecast, for the Brier skill.

## Results

From the latest run of `notebooks/02_direction_model.ipynb`, on 69 Musk DOGE post days in 2021. Every table is in [`model_findings.md`](../presentation/model_findings.md).

| Test | Horizon | n | Model | No-skill | p | Always majority | Momentum | AUC | Brier skill |
|---|---|---|---|---|---|---|---|---|---|
| **Walk-forward (Apr–Dec)** | **1d (pre-registered)** | 52 | **50%** | 49% | 0.525 | 48% | 40% | 0.52 | −0.05 |
| Walk-forward | 3d | 52 | 62% | 49% | 0.052 | 48% | 56% | 0.59 | +0.07 |
| Walk-forward | 7d | 51 | 49% | 50% | 0.620 | 55% | 59% | 0.44 | −0.10 |
| **Held-out Sep–Dec** | **1d (pre-registered)** | 20 | **20%** | 40% | 0.982 | 35% | 30% | 0.36 | −0.35 |
| Held-out Sep–Dec | 3d | 20 | 55% | 52% | 0.483 | 55% | 50% | 0.60 | +0.02 |
| Held-out Sep–Dec | 7d | 19 | 53% | 57% | 0.735 | 58% | 68% | 0.53 | −0.05 |

**Reading it:**

- **1 day (the pre-registered horizon): no skill.** The walk-forward result is at chance.
  The held-out months are worse than chance: the Jan–Aug model called DOWN on 17 of 20 autumn post days, but DOGE rose the next day after 13 of them.
- **3 days: a lead, not a finding.** 62% vs. 49%, and both permutation tests give a hit-rate p of 0.03 (outcomes shuffled, and only Musk's text features shuffled).
  But it's one of three horizons tested, so it misses the Bonferroni bar of 0.017, and on the held-out months it shrinks to 55% vs. 52%.
- **Market features flip between regimes.** Market-only models rank worse than chance (AUC 0.31–0.36). What predicted "up" during the spring mania pointed the wrong way in the autumn.
- **Conviction isn't informative yet.** On the 1d walk-forward, HIGH-conviction calls hit 45% (n = 11) and LOW 48% (n = 23).

Coefficients of the shipped 1d model (log-odds per SD, fit on all of 2021):

- 7-day momentum +0.32;
- number of posts −0.25;
- used any sentiment word −0.24;
- saying "Doge" outright +0.21;
- original post +0.12.

See `presentation/figures/08_model_coefficients.png`.

## JSON format

```json
{
  "horizon_days": 1,
  "features": ["lex_score", "lex_any", "..."],
  "intercept": 0.157,
  "coef_per_sd": [0.108, "..."],
  "train_mean": [0.075, "..."],
  "train_sd": [0.211, "..."],
  "base_rate_up": 0.536,
  "n_train_days": 69,
  "l2": 5.0,
  "conviction_edges": [0.2, 0.4],
  "meta": {"walk_forward_test": {"hit_rate": 0.5, "auc": 0.516, "...": "..."}, "heldout_test": {"...": "..."}, "...": "..."}
}
```

Scoring without this repo: `z = (x − train_mean) / train_sd` (missing → 0), then `p_up = 1 / (1 + exp(−(intercept + Σ coef·z)))`.

## Limitations

- **Small sample.** One account and one year give 69 post days, about 50 of them out-of-sample per horizon.
- **Regime change.** Feb–May 2021 was a mania and Sep–Dec a slow bleed. Market features that pointed up in spring pointed down in autumn.
- **Extreme inputs.** The late-January 2021 run-up gives `mom_7d` values about 6 SD from the mean, so early-February post days get near-certain probabilities.
  That's the 94% in the CLI example above. Clipping standardized features at ±3 would be the next variant to pre-register.
- **Invisible posts.** Image-only memes, and posts that move DOGE without saying "Doge", are invisible.
- **Daily resolution.** Daily closes blur a minutes-scale reaction.

## Retraining

1. Add posts to `data/raw/tweets/` and prices to `data/raw/prices/`.
2. Widen `analysis_start`, `analysis_end` and `train_end` in the notebook's setup cell.
3. Run `notebooks/02_direction_model.ipynb` top to bottom. It overwrites `models/*.json`, the charts and `presentation/model_findings.md`.
