# Presentation: 2 minutes

| File | Use it for |
|---|---|
| **This file** | The goal in one sentence, the run-of-show, the word-for-word script, background facts, Q&A prep |
| [`presentation_guide.md`](presentation_guide.md) | Read 15 minutes before you go on: the numbers you'll say (with sources), what must land on each slide, how to explain the model |
| [`findings.md`](findings.md) | Keyword-list results (notebook 01). Overwritten automatically by the notebook. |
| [`model_findings.md`](model_findings.md) | Trained-model results (notebook 02). Overwritten automatically by the notebook. |
| [`formatting_guide.md`](formatting_guide.md) | How to format the slides, plus a pre-flight checklist |
| `figures/` | Slide-ready charts: `01`–`05` from notebook 01 (keyword list), `06`–`08` from notebook 02 (model) |
| [`../models/README.md`](../models/README.md) | The prediction function: how to call it and what it returns |

---

## The goal (say it in one breath)

> **We tested whether Elon Musk's 2021 Dogecoin posts can call DOGE's next daily move, up or down, and how confident each call should be.
> We used an explainable keyword list and a small trained model, and scored both on months they never saw.**

## Run-of-show: 5 slides, 1:50 spoken

The script below is about 275 words, which is about 1:50 at a normal pace. Keep 10 seconds of slack.

| # | Time | Slide title (the takeaway) | On screen | Figure |
|---|---|---|---|---|
| 1 | 0:00–0:15 | **Can a Musk post call Dogecoin's next move?** | Title, team names, hook: "Dogefather" tease about +20%, "hustle" joke about −30% at the low (sources small: Newsweek, CNBC) | none |
| 2 | 0:15–0:45 | **Musk's posts → keywords + a trained model → a call with a conviction level** | Pipeline: *105 posts on 69 days → keyword score + how he posted + recent price → logistic regression → P(up) → UP/DOWN + LOW/MED/HIGH*. Below it: "Settings fixed first · tested on months it never saw" | none (simple shapes) |
| 3 | 0:45–1:10 | **On months it never saw, next-day calls were no better than chance** | Hero: **50% vs. 49%** no-skill, with "n = 52 post days, walk-forward Apr–Dec 2021" small underneath. Second line, body size: "Held-out Sep–Dec: 20% vs. 40%, n = 20" | `06_model_vs_baselines.png`, cropped to the 1-day bars |
| 4 | 1:10–1:30 | **Only 19 of Musk's 105 DOGE posts had a sentiment word** | Hero: **19 of 105**. Small: "so the keyword list called 17 of 69 post days" | `01_timeline.png` (the few dots are the point) |
| 5 | 1:30–1:50 | **Too little data to settle it. Next: more accounts, more years** | "One account, one year: about 50 test days" · "Next: more accounts, more years" | none |

**Backup slides (Q&A only):** the full `06` chart (3-day bars), `07_model_heldout_calls.png` (every held-out call),
`08_model_coefficients.png` (what the model learned, in-sample), and `05_signal_vs_buy_and_hold.png` (illustrative, no trading costs).
Why these figures were chosen is in [`presentation_guide.md`](presentation_guide.md#2-what-must-land-on-each-slide).

## Script (about 275 words)

> **[Slide 1]** In April 2021, Elon Musk posted he'd host SNL as "the Dogefather," and Dogecoin jumped about 20 percent.
> On the show he joked it was "a hustle," and it fell about 30 percent at its low. Can his posts call DOGE's next move?
>
> **[Slide 2]** We took Musk's 105 DOGE posts from 2021, on 69 days. A keyword list built for crypto slang scores the words.
> A trained model then adds how he posted, like how often and whether he said "Doge" outright, and what the price just did.
> It outputs the chance DOGE rises, which becomes a call, up or down, and a conviction: how sure it is.
> We fixed every setting first, then tested on months it never saw.
>
> **[Slide 3]** The answer: no better than chance. Refit every month from April to December, the model called the next day
> right 50 percent of the time. A blind guesser with the same mix of up and down calls gets 49.
> Trained once on January to August, it scored below chance on September to December: 20 percent against 40, over just 20 days.
>
> **[Slide 4]** Why so hard? Only 19 of Musk's 105 DOGE posts had any sentiment word at all. Most are terse: a bare "Doge,"
> an emoji, a meme. So the keyword list called just 17 of the 69 days, and those calls didn't reliably beat chance either.
>
> **[Slide 5]** The caveat: one account and one year give about 50 test days, so a 10-point edge is within noise.
> The one hint is three days out: 62 percent against 49. But we tested three horizons, so it doesn't clear the bar.
> Next: more accounts and more years, to test that hint. Thank you.

## Background facts you can cite (sourced news, not our results)

All of these come from [`data/reference/key_events.csv`](../data/reference/key_events.csv), where each one has a source link.

- **Musk events dominate the big moves.** His Feb 4 2021 post storm (DOGE up more than 50% that day), the SNL "Dogefather" tease
  (Apr 28 2021, about +20%), and the Tesla-merch-in-DOGE announcement (Dec 14 2021, up to +23% intraday).
- **Sell the news.** Hype peaked *before* the scheduled events: the Dogeday 4/20 push (about −20% over 24h) and SNL night itself (as much as −30% after the "hustle" joke).
- **Not every crash was post-driven.** Tesla suspending Bitcoin payments (May 12 2021) and China's crypto crackdown (May 19 2021) hit all of crypto.
- **Text has blind spots.** The archive has *no* text post from Musk mentioning DOGE in January 2021, the month of the WallStreetBets spike; his DOGE posts then were likely images.
- **Keywords misread context.** In "Super important for Doge fees to *drop*…", the keyword list reads "drop" as bearish, though Musk meant cheaper transactions
  (a later "buying" happens to cancel it out). That's a held-out post day (2021-09-22): the model called DOWN with HIGH conviction, and DOGE rose.

## Q&A prep (likely questions)

| Question | Short answer |
|---|---|
| "Why is the held-out test so much worse than walk-forward?" | Two reasons we can't separate. The held-out model learned once, from Jan–Aug (mostly the mania), and never updated; walk-forward relearns every month. 2021 changed regime, from mania to slow bleed, and relationships learned in Feb–May can flip by the autumn: in `07` it called DOWN on most Sep–Dec post days, and most of those were wrong. And it's only 20 days, so luck is a big part of any gap. Neither test is distinguishable from chance. |
| "Isn't 62% at three days a result?" | It's a lead, not a finding. Walk-forward 3-day calls hit 62% vs. 49% no-skill (n = 52, p = 0.052), and a permutation test gives p = 0.030. Shuffling only Musk's text features also gives p = 0.030, a hint the words add something at three days. But we tested three horizons, so the bar is 0.017, and neither clears it. Held-out 3-day was 55% vs. 52% (p = 0.483). The 1-day focus was chosen before testing, so we don't switch to the best-looking horizon afterwards. |
| "Did you have look-ahead?" | Each post is anchored to the nearest daily close (at most 12h of overlap), and the outcome is measured from that close. Market features use prices up to it; text features use only the posts. Likes and reposts are left out because they keep growing after the post. Training only uses post days whose outcome was already known before the test period starts (a purge), so no 3- or 7-day window crosses into the test. Features are scaled with training-period means and SDs only. |
| "Why logistic regression?" | We have 69 post days; anything flexible would memorize noise. Logistic regression gives a probability (which sets the conviction), every weight is readable as a push per SD of one feature, and the L2 penalty (5, fixed in advance) shrinks the weights toward the base rate. A fancier model can't fix too little data. |
| "How do I use the prediction function?" | `python scripts/predict.py "<post text>" --at <UTC time>`. For each horizon it prints the call, P(up), the conviction, the features that pushed it most, and what DOGE actually did if our prices cover it. In Python: `Predictor.from_repo().predict(text, posted_at=...)`. It needs DOGE prices up to the post's anchor close (add current prices to score a post from today). The shipped models are fit on all of 2021, so any 2021 post is in-sample; notebook 02's "Use it: score new posts" section shows an honest demo with the Jan–Aug model. Reference: [`models/README.md`](../models/README.md). |
| "Does conviction mean anything?" | Not yet. Walk-forward 1-day: HIGH hit 45% (n = 11), MEDIUM 56% (n = 18), LOW 48% (n = 23), so HIGH didn't beat LOW. The keyword list has too few days per bucket to judge (high 60%, n = 5; low 33%, n = 6). |
| "Is it the words or the market?" | Walk-forward 1-day: text only 52%, market only 37%, both 50%. Shuffling only Musk's text features at 1 day gives p = 0.415, so there's no sign the words add anything there. |
| "What did the model learn?" (`08`) | Fit on all of 2021: DOGE's 7-day return pushes toward UP (+0.32 per SD); more posts that day (−0.25) and using any sentiment word (−0.24) push toward DOWN. That's in-sample, and the model has no proven skill, so it's a description, not a discovery. |
| "Isn't this just Elon?" | Yes, by design. He's the account with documented price moves, and the scope is @elonmusk only: 105 posts on 69 post days in 2021. More accounts is the next step, and the main way past about 50 test days. |
| "Did you overfit?" | Features, the penalty, the horizons and the 1-day focus were fixed before testing, and nothing was tuned on test months. For the keyword list, conviction cutoffs and learned keywords were fit on Jan–Aug only, and lexicon terms inspired by specific 2021 events were removed to avoid hindsight. |
| "Why not a big language model?" | Explainability, and data. Every call lists what drove it. With 69 post days the limit is the data, not the reader. An LLM scorer is a natural next comparison. |
| "Couldn't you trade this?" | No. It isn't distinguishable from chance at the 1-day horizon we chose in advance, and there are no trading costs and only daily prices. `05_signal_vs_buy_and_hold.png` is illustrative only. |
| "Why is the baseline not 50%?" | DOGE's share of up-days changed a lot during 2021. The bar is the hit rate a no-skill caller would get given how often DOGE rose and how often the model called UP: 49% for walk-forward and 40% for held-out (1-day). |
