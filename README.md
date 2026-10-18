# 🐕 Dogebone

**Do posts from Dogecoin's most influential accounts call DOGE's next daily move?**
This is an explainable keyword/lexicon NLP pipeline. For every post (and every day) it outputs a **direction** (UP / DOWN / no call) and a **conviction** (LOW / MEDIUM / HIGH),
then scores those calls against DOGE daily closes from **Jan 2021 to Dec 2022**: calibrated on 2021, tested out-of-sample on 2022.

📄 **Start with [`PROJECT_BRIEF.md`](PROJECT_BRIEF.md)** for the goal, the hypotheses, the 10 accounts, the method and the 60-minute plan.
🎤 **Presenting?** See [`presentation/`](presentation/).

## Quickstart

```bash
pip install -r requirements.txt
jupyter lab notebooks/01_doge_post_sentiment_signal.ipynb   # Run All
```

The notebook runs immediately on **synthetic** sample data (`data/sample/`), which carries a planted signal so you can see the pipeline work.
Results are bannered and charts are watermarked "SYNTHETIC DATA" until real data is present.

**To use real data:**

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
├── notebooks/01_doge_post_sentiment_signal.ipynb   the analysis, end to end
├── src/dogebone/              the pipeline the notebook calls
│   ├── config.py              every knob (horizons, anchoring, thresholds, train/test split)
│   ├── io.py                  tolerant loaders for prices and tweet exports
│   ├── text.py                normalization, emoji-aware tokenizer, coin-context tagger
│   ├── lexicon.py             explainable scorer (phrases, negation, intensifiers, hedges, caps)
│   ├── market.py              post→close anchoring, forward returns, event-study paths
│   ├── signals.py             direction + conviction, daily aggregation
│   ├── evaluate.py            hit rate vs. no-skill/momentum baselines, keyword discovery
│   ├── plots.py               slide-ready charts
│   └── report.py              drafts presentation/findings.md from results
├── presentation/              2-minute talk: outline, script, formatting guide, findings, figures
└── scripts/make_sample_data.py
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
- **The rule:** tune only on **2021** posts. Looking at 2022 while tuning leaks the test set, and the out-of-sample number stops meaning anything.
