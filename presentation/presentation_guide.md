# Presentation guide: Dogebone in 2 minutes

Read this 15 minutes before you go on. It covers the numbers you'll say, what must land on each slide, and how to explain the work.
The run-of-show, the word-for-word script and the Q&A answers are in [`README.md`](README.md).

> **Results are final for this scope:** @elonmusk only, 105 DOGE posts on 69 post days, 2021. Every result number in this file is copied from
> [`findings.md`](findings.md) (keyword list, notebook 01) or [`model_findings.md`](model_findings.md) (trained model, notebook 02).
> If either notebook is re-run, re-check this table against those files. If anything says **SYNTHETIC DATA** or **Pending real data**, stop.

## The numbers you'll say

| What | Say it as | Source |
|---|---|---|
| Data | 105 Musk DOGE posts on 69 post days, 2021 | `model_findings.md`, header line |
| **Headline: walk-forward**, 1-day (Apr–Dec, refit monthly) | **50% vs. 49%** no-skill, n = 52, p = 0.525 | `model_findings.md` → Headline, 1st bullet |
| **Headline: held-out**, 1-day (trained Jan–Aug, tested Sep–Dec) | **20% vs. 40%** no-skill, n = 20, p = 0.982 | `model_findings.md` → Headline, 2nd bullet |
| Posts with any sentiment word | 19 of 105 (18%) | `findings.md` → Coverage |
| Post days the keyword list called | 17 of 69 | `findings.md` → Coverage |
| Keyword list, full year, 1-day | 53% vs. 48% no-skill, n = 17, p = 0.437 | `findings.md` → Headline, 1st bullet |
| The 3-day hint (walk-forward) | 62% vs. 49%, n = 52, p = 0.052; permutation p = 0.030 | `model_findings.md` → Every horizon table; Permutation tests |
| The bar for three horizons | p below 0.017 (Bonferroni) | `model_findings.md` → note under the Every horizon table |
| Sample-size caveat | about 50 test days per horizon, so a 10-point edge is within noise | `model_findings.md` → Caveats, 1st bullet |

Every test result in this table is either "not distinguishable from chance" or misses the 0.017 bar. Say exactly that on stage.

---

## 1. The project

**In one sentence:** Dogebone tests whether Elon Musk's 2021 DOGE posts can call whether DOGE closes up or down a day later, and how much to trust each call,
using an explainable keyword list and a small trained model, both scored on months they never saw.

- **Problem.** DOGE is the clearest case of a market moved by social media: no cash flows, uncapped supply, and a 2021 run driven openly by posts and memes. The open question is whether the posts carry a signal, or just echo the price.
- **Approach.** Two tools, one pipeline:
  1. **Keyword list** (notebook 01). A scored dictionary of crypto terms and emoji, with rules for negation and hedging, turns each post into a score from −1 to +1. A post day gets UP / DOWN / no call, with a conviction level.
  2. **Trained model** (notebook 02, `src/dogebone/model.py`). An L2 logistic regression on each post day. Text features: the keyword score, whether any sentiment word was used, how many posts, the share saying "Doge" outright (vs. replies that only tag a DOGE account), original post vs. replies only, and days since the previous DOGE post. Market features: recent DOGE returns, recent volatility, and distance below the recent high. It outputs P(DOGE up) after 1, 3 and 7 days, then a call (UP / DOWN) and a conviction (LOW / MEDIUM / HIGH). Full feature list: [`models/README.md`](../models/README.md).
- **How it was tested.** The features, the penalty, the horizons and the 1-day focus horizon were all fixed before testing. Then two tests:
  - **Held-out:** train on Jan–Aug, predict every Sep–Dec post day once.
  - **Walk-forward:** at each month start (Apr–Dec), refit on earlier post days whose outcome is already known, then predict that month.
  - Baselines on the same days: the no-skill rate, always calling the training majority, and momentum.
- **Why it's interesting.** Every call explains itself (the matched words, or the model's top features). The 1-day focus was chosen before testing, so the headline isn't cherry-picked. And a clean "no" is a real finding.

## 2. What must land on each slide

1. **Hook.** Same person, different words, opposite moves. These are reported price moves from [`key_events.csv`](../data/reference/key_events.csv), not model output.
2. **Method.** One picture: *posts → keyword score + how he posted + recent price → P(up) → call + conviction*. Define conviction once ("how sure it is").
   Say "settings fixed first, tested on months it never saw." That's your strongest credibility line.
3. **Headline.** Lead with walk-forward, the bigger test: 50% vs. 49%, n = 52. Then held-out in the same breath: 20% vs. 40%, over just 20 days.
   Keep the held-out line at body size, not in a footnote. It's the worse number, and shrinking it costs credibility. Don't explain it away on stage; the reasons are in the Q&A.
4. **Supporting insight: the posts are mostly wordless.** This is the most defensible insight because it's a count, not a test: 19 of 105 posts, 17 of 69 post days called. It also explains why the model reads *how* Musk posted, not only *what* he said.
5. **Close.** One caveat (about 50 test days; a 10-point edge is within noise), the one hint (3-day: 62% vs. 49%, which misses the bar), one next step (more accounts, more years). Then "Thank you." Stop talking.

**Figure choices**

| Figure | Use it for | Why |
|---|---|---|
| `06_model_vs_baselines.png` | Slide 3, cropped to the 1-day bars. Full chart is the backup for the 3-day question. | The model bar sits on the no-skill line. Cropping keeps the 3-day bar from stealing the slide. |
| `01_timeline.png` | Slide 4. Crop out its title. | A whole year of price with only a few dots: that's how rarely the keyword list fires. |
| `07_model_heldout_calls.png` | Backup: "why is held-out worse?" | Every Sep–Dec post day: mostly DOWN calls during the slide, most of them wrong. |
| `08_model_coefficients.png` | Backup: "what did it learn?" | Fit on all of 2021, so it's in-sample. It describes the model; it isn't evidence of skill. |
| `02`–`05` | Backup only | Keyword-list charts with very small n (e.g. 5 high-conviction days). |

**Other slide-4 options** (only if you'd rather; both are less defensible than the coverage count):

- *The 3-day hint* (full `06` chart): 62% vs. 49%, and shuffling only the text features gives p = 0.030. Always add "but with three horizons the bar is 0.017." If you use it here, drop the hint from slide 5.
- *The regime flip* (`07`): trained on the spring mania, the model called DOWN on most autumn post days and was mostly wrong. Present it as an explanation, not a test.

## 3. Explaining the method to a non-technical judge (20 seconds)

> "Two readers. The keyword list is a scored dictionary of crypto words and emoji. The model is a weighted checklist: how many posts,
> did he say 'Doge' or just reply, was there any sentiment word, what did the price do last week. It adds the weights into a probability
> that DOGE is up tomorrow. More likely up is an UP call; the more sure it is, the higher the conviction. We fixed it all first and judged it
> on months it never saw. The bar isn't a coin flip. It's what a blind guesser with the same mix of ups and downs would score."

| Piece | Plain English | Detail if asked |
|---|---|---|
| Keyword list | A dictionary with points: "to the moon" +3, "rug pull" −3.5, 🚀 +2.5 | `lexicons/sentiment_lexicon.csv`. Longest phrase wins, so "pump and dump" isn't scored as "pump". Rules follow VADER. |
| Post day | All of Musk's DOGE posts measured from the same daily close | Each post is anchored to the nearest daily close (at most 12h of overlap) |
| Trained model | A weighted checklist that turns a post day into P(up) | L2 logistic regression, penalty 5, fixed in advance. Each weight is the push on the log-odds per SD of one feature. |
| Call + conviction | More likely up means UP. LOW = P(up) between 40% and 60%; HIGH = at least 70% sure either way | Note under the conviction table in `model_findings.md` |
| Two tests | Held-out: learn Jan–Aug, test Sep–Dec once. Walk-forward: relearn every month from the past only | Training rows need their outcome known before the test period starts, so no window crosses the line |
| No-skill baseline | If DOGE rose most days and you always said "up," you'd look smart by luck. This is the rate to beat | The hit rate expected if calls ignored outcomes, given how often the model said UP and how often price rose |

**One post, scored by the keyword list** (the project's own scorer, current lexicon; illustrative posts, not real ones):

| Post | Words matched (points) | Score, −1 to +1 | Call |
|---|---|---|---|
| "Dogecoin to the moon 🚀🚀" | to the moon +3.0, 🚀 +2.5, 🚀 +2.5 (total +8.0) | **+0.90** | UP, strong |
| "Maybe $DOGE to the moon?" | to the moon +3.0, then *maybe* and the `?` shrink it | **+0.44** | UP, weaker |
| "Not bullish on $DOGE. Looks like a pump and dump." | bullish −2.2 (negated), pump and dump −3.0 | **−0.80** | DOWN, strong |

If the lexicon gets tuned, re-check these with `scorer.explain(...)` or notebook 01 section 13.

## 4. Framing the result: it's a null, and that's fine

- **Say "no reliable evidence," not "it predicts" and not "it's useless."** Both 1-day tests are "not distinguishable from chance."
- **Held-out below chance:** say it plainly, "20% vs. 40%, over just 20 days." Don't spin it.
- **The 3-day hint is a lead, not a result.** p = 0.052 (permutation p = 0.030) misses the 0.017 bar for three horizons, and held-out 3-day was 55% vs. 52%. Never put it in a slide title.
- **Conviction didn't separate good calls from bad.** Walk-forward HIGH-conviction calls hit 45% (n = 11) vs. 48% for LOW (n = 23). Don't claim the confidence levels work.
- **Don't apologize.** A well-explained null beats an oversold result.

## 5. Questions to rehearse

All answers are in [`README.md`](README.md#qa-prep-likely-questions). Say these four out loud once before you go on:
why is held-out worse than walk-forward; isn't 62% at three days a result; did you have look-ahead; why logistic regression.

## 6. Don't

- **Don't oversell.** No "predicts," "alpha," or "beats the market." The model is "not distinguishable from chance."
- **Don't quote 62% without its caveat.** It always travels with "misses the bar for testing three horizons."
- **Don't demo live in the 2 minutes.** For Q&A, keep a terminal open with `python scripts/predict.py "<post text>" --at <UTC time>` ready.
- **Don't show tables on slides.** One hero number with its baseline, or one chart.
- **Don't show a number without its baseline and n.** "50% vs. 49%, n = 52" and "20% vs. 40%, n = 20" always travel together.
- **Don't type numbers from memory.** Copy them from the table at the top of this file.
- **Don't present anything marked SYNTHETIC DATA**, and don't use `05_signal_vs_buy_and_hold.png` as a trading claim.
- **Don't present `08_model_coefficients.png` as a finding.** It's fit on all of 2021, and the model has no proven skill.
- **Don't claim a "bear-market test".** Sep–Dec 2021 was a slow bleed after the mania, not 2022.
- **Don't blur background and results.** The SNL moves are reported news, not model output.

## 7. Formatting: the four rules that matter

Everything else is in [`formatting_guide.md`](formatting_guide.md).

1. **Titles are takeaways.** A judge who reads only the five titles should get the whole story.
2. **One hero number per results slide**, 60pt or larger, with the baseline right beside it and `n` small underneath. Round to whole percentages.
3. **Use the exported PNGs as-is, one per slide**, cropped to the panel that matters. The color code is blue = UP/bullish, red = DOWN/bearish, gray = baseline/price, violet = the model's hit rate.
4. **No more than 15 words of body text per slide.** The script carries the detail.

## Last check before you walk on

- [ ] `findings.md` and `model_findings.md` have no SYNTHETIC or Pending banner, and no chart has a watermark.
- [ ] Every number on a slide matches the table at the top of this file, and that table matches the latest findings files.
- [ ] Slide 3 shows both tests, each with its baseline and `n`.
- [ ] Slides open offline, with charts embedded.
- [ ] Timed run-through at 1:50 or less. The first sentence is memorized.
