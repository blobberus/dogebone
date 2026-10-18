# Presentation: 2 minutes

| File | Use it for |
|---|---|
| **This file** | The goal in one sentence, the slide-by-slide run-of-show, a word-for-word script, background findings, Q&A prep |
| [`findings.md`](findings.md) | **Analysis findings with real numbers.** Overwritten automatically by the notebook's last section. |
| [`formatting_guide.md`](formatting_guide.md) | How to format the slides, plus a pre-flight checklist |
| `figures/` | Slide-ready charts exported by the notebook (watermarked "SYNTHETIC DATA" until real data is used) |

---

## The goal (say it in one breath)

> **We tested whether the words in posts from the 10 most influential Dogecoin accounts can call DOGE's next daily move, up or down,
> and how confident each call should be. We used an explainable keyword model trained on 2021 and tested on 2022.**

## Run-of-show: 5 slides, 2:00 total

Two minutes is about **270 spoken words**. Budget **1:50** and keep 10 seconds of slack.

| # | Time | Slide title (the takeaway) | On screen | Figure |
|---|---|---|---|---|
| 1 | 0:00–0:15 | **Can tweets call Dogecoin's next move?** | Title, team names, one hook stat | none |
| 2 | 0:15–0:40 | **10 accounts → keywords → a call with a confidence level** | 3-step pipeline graphic: *posts → keyword score → UP/DOWN + Low/Med/High* and "Train 2021 · Test 2022" | none (simple shapes) |
| 3 | 0:40–1:15 | **[Headline from `findings.md`, e.g. "High-conviction calls were right [X]% of the time vs. [Y]% by chance"]** | One hero number and its baseline | `02_hit_rate_by_conviction.png` (crop to the 1-day panel) |
| 4 | 1:15–1:40 | **[One supporting insight, e.g. "Posts lead price for about a day, then the edge fades"]** | One chart | `03_event_study.png` **or** `04_keywords.png` **or** `01_timeline.png` |
| 5 | 1:40–2:00 | **What it means, and what it can't tell you** | One caveat, one next step | none |

**Choosing slide 4.** Use the event study if posts lead price (the lines split after day 0). Use the keywords chart if the learned words are intuitive.
Use the timeline if the story is "the edge lives in a handful of Musk events".

## Script (~270 words; fill in the brackets from `findings.md`)

> **[Slide 1]** In 2021, one post from Elon Musk teasing his SNL appearance moved Dogecoin about 20% in a day. So we asked:
> can the *words* in these posts tell us where DOGE goes next?
>
> **[Slide 2]** We took every DOGE post from the ten most influential accounts: Musk, the co-creator Billy Markus, Mark Cuban, the
> Dogecoin Foundation, and others. A keyword model, built for crypto slang (it knows "to the moon" is bullish, "not bullish" isn't,
> and "pump and dump" isn't a pump), scores each post. The output is a direction, up or down, plus a conviction level. We tuned
> everything on 2021 and tested it untouched on 2022, a completely different bear market.
>
> **[Slide 3]** The result: on 2022 data the model called the next day's direction correctly **[X]%** of the time. A coin flip,
> adjusted for how often DOGE actually rose, gets **[Y]%**. And conviction matters: high-conviction calls hit **[Z]%**.
>
> **[Slide 4]** **[Pick one]** The edge is short-lived: it shows up the next day and is gone by day three. *Or:* The words that
> mattered most were **[top keywords]**. *Or:* Most of the signal comes from a handful of Musk moments.
>
> **[Slide 5]** Two honest caveats. Daily prices blur a reaction that happens in minutes, and keywords can't read memes or
> sarcasm. So this is a confidence signal, not a trading bot. Next we'd add intraday prices and image understanding. Thank you.

**If the result is null** (p ≥ 0.05, or no better than momentum), say so. It's still a strong talk:
*"Even the most famous Dogecoin posts didn't reliably call the next move once you account for how often DOGE goes up anyway.
Posts mostly echoed price instead of leading it."* Keep slides 3–4 and swap the headline.

## Background findings you can cite now (sourced; not from our model)

All of these come from [`data/reference/key_events.csv`](../data/reference/key_events.csv), where each one has a source link.

- **Musk events dominate the big moves.** The SNL "Dogefather" tease (Apr 28 2021, about +20%), the Twitter stake (Apr 4 2022, about +10%),
  the board accepting his buyout (Apr 25 2022, about +20%), and the Twitter close (Oct 28 2022, DOGE roughly doubled over the following days).
- **Sell the news.** Hype peaked *before* the scheduled events: the Dogeday 4/20 push (about −20% over 24h) and SNL night itself (as much as −30% after the "hustle" joke).
- **2022's biggest drops weren't post-driven.** LUNA (May), Celsius (Jun) and FTX (Nov) were crypto-wide crashes, which is why the notebook can compare against BTC-adjusted returns.
- **Text has blind spots.** Many of Musk's DOGE posts were image-only memes, and some major moves followed posts that never said "DOGE" at all (Oct 2022, "the bird is freed").

## Q&A prep (likely questions)

| Question | Short answer |
|---|---|
| "Isn't this just Elon?" | Check the per-account table in notebook section 7. Musk has the top influence weight, but every account is scored separately. |
| "Did you overfit?" | Conviction cutoffs and learned keywords were fit on 2021 only, and 2022 was never looked at while tuning. Section 7 also has a robustness check that drops days around 34 key events. |
| "Why not a big language model?" | Explainability and speed. Every call lists the exact words that drove it. An LLM scorer is a natural next step to compare against. |
| "Couldn't you trade this?" | No costs, daily data, one coin. The equity curve in section 11 is illustrative only. |
| "Why is the baseline not 50%?" | DOGE's share of up-days differs a lot between the 2021 mania and the 2022 bear market (notebook section 5 shows both). The bar is the hit rate a no-skill caller would get given those rates and how often we called UP. |
