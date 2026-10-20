# 🐕 Dogebone

**Do posts from Dogecoin's most influential accounts call DOGE's next daily move?**
This is an explainable keyword/lexicon NLP pipeline. For every post (and every day) it outputs a **direction** (UP / DOWN / no call) and a **conviction** (LOW / MEDIUM / HIGH),
then scores those calls against DOGE daily closes for **2021**: calibrated on Jan–Aug, tested out-of-sample on Sep–Dec.

**Current data:** every DOGE-related post by **@elonmusk in 2021** (105 posts, from a public archive) and the team's DOGE daily prices.
Latest results: [`presentation/findings.md`](presentation/findings.md) (lexicon calls) and
[`presentation/model_findings.md`](presentation/model_findings.md) (trained model).

🤖 **Trained model:** [`models/README.md`](models/README.md) documents the prediction function. It estimates P(DOGE up over 1, 3 or 7 days)
after a Musk DOGE post, with a call, a conviction and the reasons:

```bash
python scripts/predict.py "Dogecoin is the people's crypto" --at 2021-02-04T08:00:00Z
```

📄 **Start with [`PROJECT_BRIEF.md`](PROJECT_BRIEF.md)** for the goal, the hypotheses, the 10 accounts, the method and the 60-minute plan.
🎤 **Presenting?** See [`presentation/`](presentation/).

## Quickstart

```bash
pip install -r requirements.txt
jupyter lab notebooks/01_doge_post_sentiment_signal.ipynb   # lexicon calls: Run All
jupyter lab notebooks/02_direction_model.ipynb              # trained model: train, test, export models/
```

The notebook runs on the **real data already in `data/raw/`**. To rebuild those files from source:

```bash
python scripts/fetch_musk_tweets.py --year 2021   # public archive (~42 MB) -> data/raw/tweets/elonmusk_2021.csv
python scripts/prepare_doge_prices.py             # data/raw/prices/DogePrice.xlsx -> data/raw/prices/doge_daily.csv
```

If `data/raw/` is empty, the notebook falls back to **synthetic** sample data (`data/sample/`, with a planted signal); results are then
bannered and charts watermarked "SYNTHETIC DATA".

**To add more accounts or other data:**

1. Put a DOGE daily price CSV (file name containing `doge`) in `data/raw/prices/`. Optionally add a `btc` file for market-adjusted returns.
2. Put the tweet export(s) in `data/raw/tweets/`. CSV, JSON and JSONL all work; most scraper column names are mapped automatically. See [`data/README.md`](data/README.md).
3. Re-run the notebook. It writes `presentation/findings.md` and the slide charts in `presentation/figures/`.

Google Colab works too: uncomment the `git clone` line in the first code cell.

## Repository layout

```
dogebone/
├── PROJECT_BRIEF.md           goal, hypotheses, the 10 accounts, method, hackathon plan
├── config/accounts.csv        10 primary + 5 alternate accounts, influence weights, collection notes
├── lexicons/                  ← tune the NLP here, no code changes needed
│   ├── sentiment_lexicon.csv  ~220 crypto terms/phrases/emoji with weights (-4..+4)
│   ├── modifiers.csv          negators, intensifiers, diminishers, hedges
│   └── doge_context.csv       cues that a post is about the coin (vs. a bare meme)
├── data/
│   ├── raw/{prices,tweets}/   ← drop real data here
│   ├── sample/                synthetic test data (scripts/make_sample_data.py)
│   ├── reference/key_events.csv  34 sourced DOGE events, 2021-2022
│   └── processed/             notebook outputs (git-ignored)
├── notebooks/
│   ├── 01_doge_post_sentiment_signal.ipynb   lexicon calls vs. price, end to end
│   └── 02_direction_model.ipynb              trained up/down model: held-out + walk-forward tests, exports models/
├── models/                    saved models (JSON, one per horizon) + README for the prediction function
├── src/dogebone/              the pipeline the notebook calls
│   ├── config.py              every knob (horizons, anchoring, thresholds, train/test split)
│   ├── io.py                  tolerant loaders for prices and tweet exports
│   ├── text.py                normalization, emoji-aware tokenizer, coin-context tagger
│   ├── lexicon.py             explainable scorer (phrases, negation, intensifiers, hedges, caps)
│   ├── market.py              post→close anchoring, forward returns, event-study paths
│   ├── signals.py             direction + conviction, daily aggregation
│   ├── evaluate.py            hit rate vs. no-skill/momentum baselines, keyword discovery
│   ├── model.py               post-day features, logistic model, out-of-sample tests, Predictor
│   ├── pipeline.py            raw files -> scored, anchored posts in one call
│   ├── plots.py               slide-ready charts
│   └── report.py              drafts presentation/findings.md and model_findings.md from results
├── presentation/              2-minute talk: outline, script, formatting guide, findings, figures
└── scripts/                   predict.py, fetch_musk_tweets.py, prepare_doge_prices.py, xlsx_to_csv.py, make_sample_data.py
```

## How a call is made

```python
from dogebone import Config, lexicon
scorer = lexicon.LexiconScorer(Config())
scorer.explain("Not selling a single $DOGE. Extremely bullish 🚀🚀 but maybe wait for the dip?")
```

| term | contribution |
|---|---|
| selling | +1.48 (negated) |
| bullish | +4.20 (intensified) |
| 🚀, 🚀 | +2.50 each |
| dip | −1.00 |
| **sentiment** | **≈ +0.67** after normalization and the *maybe* / `?` hedges |

Run the rule checks with `python tests/test_pipeline.py` (or `pytest tests`).

## Tuning (and the one rule)

- **Lexicon:** edit `lexicons/sentiment_lexicon.csv`. Section 4 of the notebook shows the most bullish and bearish posts and the terms that matched.
- **Knobs:** set them in the notebook's config cell: `horizons`, `anchor_mode`, `neutral_threshold`, `train_end` (see `src/dogebone/config.py`).
- **The rule:** tune only on **Jan–Aug 2021** posts. Looking at Sep–Dec while tuning leaks the test set, and the out-of-sample number stops meaning anything.
