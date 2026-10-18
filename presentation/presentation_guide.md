# Presentation guide: Dogebone in 2 minutes

Read this 15 minutes before you go on. It covers what the project is, what's on each slide, what to say, and how to handle questions.

> **No results are written here.** Every `[BRACKET]` is filled from [`findings.md`](findings.md) after the final notebook run.
> If `findings.md` or any chart still says **SYNTHETIC DATA** or **Pending real data**, stop: those numbers can't be presented.

## Fill-ins

| Placeholder | What it is | Where to get it |
|---|---|---|
| `[WINDOW]` | **2021** (Jan 1 – Dec 31) | `findings.md` header line ("... *start* to *end*") |
| `[TRAIN PERIOD]` / `[TEST PERIOD]` | **January to August 2021** / **September to December 2021** | `train_end` in the notebook's config cell: train runs up to that date and test starts the day after |
| `[ACCOUNTS]` | **"Elon Musk"** (current data is Musk-only: 105 DOGE posts in 2021) | `findings.md` header ("by *N* accounts") and [`config/accounts.csv`](../config/accounts.csv) |
| `[HIT RATE]`, `[NO-SKILL RATE]`, `[EDGE]`, `[P VALUE]`, `[N DAYS]` | The headline result for next-day calls. If the test period has fewer than 40 called days, `findings.md` leads with the full year and lists the train/test split underneath. Say which one you're quoting. | `findings.md` → Headline, first bullet |
| `[HIGH-CONV RATE]`, `[LOW-CONV RATE]` | Hit rate on high- vs. low-conviction days | `findings.md` → "Conviction" bullet |
| `[MOMENTUM RATE]` | Hit rate of "yesterday's direction continues" | `findings.md` → "Momentum check" bullet |
| `[1D RATE]`, `[7D RATE]` | Hit rate at the 1-day and 7-day horizons | `findings.md` → "Horizon decay" bullet |
| `[TOP KEYWORDS]` | Learned words that came before up-moves / down-moves | `findings.md` → "Keywords that preceded up-moves" bullet |
| `[LEARNED RATE]`, `[LEXICON RATE]` | Test-period hit rate of the learned word list vs. the hand-built one | `findings.md` → "Hand-crafted vs. learned keywords" bullet |
| `[EX-EVENTS RATE]` | Hit rate with ±2 days around each key event dropped | Notebook section 7, robustness cell (not in `findings.md`) |

**Read `n` first.** With one account and one year, called days are few. If `findings.md` says "too few to conclude", say exactly that on stage.

---

## 1. The project

**In one sentence:** Dogebone tests whether the words in posts from `[ACCOUNTS]` can call whether DOGE's price goes up or down the next day, and how much to trust each call, using an explainable keyword model tuned on `[TRAIN PERIOD]` and tested on `[TEST PERIOD]`.

- **Problem.** DOGE is the clearest case of a market moved by social media: no cash flows, uncapped supply, and a 2021 run driven openly by posts and memes. The open question is whether the *words* carry a signal, or whether posts just echo the price.
- **Approach.** A crypto keyword model (about 220 terms and emoji, plus rules for negation and hedging) turns each day's posts into a call (**UP / DOWN / no call**) with a **conviction** level (**LOW / MEDIUM / HIGH**). Those calls are scored on held-out data against a no-skill baseline and a momentum baseline.
- **Why it's interesting.** Every call can be explained in one sentence, because it lists the words that drove it. It tests whether confidence is *calibrated*, not just whether the direction is right. And a clean "no" answer is a real finding too.

## 2. Slide plan (1:50 total, 10 seconds of slack)

| # | Time | Takeaway title | On screen | Figure |
|---|---|---|---|---|
| 1 | 0:00–0:20 | **Can a tweet call Dogecoin's next move?** | Title, team names, the hook stat: "Dogefather" tease about +20%, "hustle" joke about −30% at the low (sources small: Newsweek, CNBC) | none |
| 2 | 0:20–0:45 | **`[ACCOUNTS]` → keywords → a call with a conviction level** | 3-step graphic: *posts → keyword score → UP/DOWN + Low/Med/High*. Below it: "Tuned: `[TRAIN PERIOD]` · Tested: `[TEST PERIOD]`" | none (simple shapes) |
| 3 | 0:45–1:10 | **Headline from `findings.md`** (strong or null version, see section 5) | Hero number `[HIT RATE]` vs. `[NO-SKILL RATE]`; small "n = `[N DAYS]` days, `[TEST PERIOD]`, out-of-sample" | `02_hit_rate_by_conviction.png`, cropped to the **1-day** panel |
| 4 | 1:10–1:30 | **One supporting insight** (pick one, see below) | One chart, with an arrow on the line or bar that matters | `03_event_study.png` **or** `04_keywords.png` **or** `01_timeline.png` |
| 5 | 1:30–1:50 | **A confidence signal, not a trading bot** | One caveat, one next step | none |

Backup only (Q&A, never a main slide): `05_signal_vs_buy_and_hold.png`. It's an illustrative test-period equity curve with no trading costs.

**Talking points: what must land on each slide**

1. **Hook.** Same person, different words, opposite moves. These are reported price moves from [`key_events.csv`](../data/reference/key_events.csv), not our model's output.
2. **Method.** Name the accounts, give one slang example, and define conviction once. Say "tested on data it never saw." That's your strongest credibility line.
3. **Headline.** One number and its baseline. Point at the HIGH bar and the no-skill line. Say whether conviction separated good calls from bad ones.
4. **Supporting insight.** Choose by what the run shows:
   - `03_event_study.png` if the bullish and bearish lines split **after** day 0 (posts lead price). This chart covers all of `[WINDOW]`, not just the test period, so don't call it out-of-sample.
   - `04_keywords.png` if the learned words are intuitive. These are learned from `[TRAIN PERIOD]` only. The notebook skips this chart when there are too few posts, so check it's from the latest run.
   - `01_timeline.png` if the edge lives in a few big Musk days. It shows price, high-conviction calls, and numbered key events.
5. **Close.** One caveat said plainly, one next step, then "Thank you." Stop talking.

## 3. Spoken script (about 240 words as written, about 260–270 once the brackets are spoken)

> **[Slide 1]** In April 2021, Elon Musk posted he'd host SNL as "the Dogefather," and Dogecoin jumped about 20 percent.
> On the show, he joked it was "a hustle," and it fell about 30 percent at its low. Can the words in these posts call DOGE's next move?
>
> **[Slide 2]** We took every DOGE post from `[ACCOUNTS]` and scored it with a keyword model built for crypto slang.
> It knows "to the moon" is bullish and "not bullish" isn't. Each day gets a call, up or down, and a conviction level:
> how strong the words are. We tuned it on `[TRAIN PERIOD]`, then tested it, untouched, on `[TEST PERIOD]`.
>
> **[Slide 3]** On `[TEST PERIOD]`, data the model never saw, it called the next day's direction right `[HIT RATE]` of the time,
> over `[N DAYS]` days. A blind guesser making the same mix of up and down calls gets `[NO-SKILL RATE]`.
> `[Strong: That's [EDGE] points better than chance. / Null: That's no better than chance.]`
> And conviction `[mattered / didn't matter]`: high-conviction days hit `[HIGH-CONV RATE]`, low-conviction days `[LOW-CONV RATE]`.
>
> **[Slide 4: say one]**
> *Event study:* Here's the average DOGE price path around our calls: blue after bullish days, red after bearish ones.
> The lines split `[after / before]` day zero, so the posts `[lead / mostly follow]` the price. And the edge `[fades / holds]`:
> `[1D RATE]` next day, `[7D RATE]` a week out.
> *Keywords:* We also let the data pick the words, using only `[TRAIN PERIOD]`. Before up-moves, the top words were
> `[TOP KEYWORDS: up]`. Before down-moves, `[TOP KEYWORDS: down]`. On the test period those learned words hit
> `[LEARNED RATE]`, vs. `[LEXICON RATE]` for our hand-built list.
> *Timeline:* This is DOGE's price across `[WINDOW]`, with our high-conviction calls as dots and the big news days numbered.
> Most of the signal sits on a few Musk days. Without them, the edge `[shrinks / holds]`: `[EX-EVENTS RATE]`.
>
> **[Slide 5]** Two honest caveats. Daily prices blur a reaction that happens within minutes, and keywords can't read
> memes, images or sarcasm. So treat this as a confidence signal, not a trading bot. Next, we'd add intraday prices,
> image understanding, and an LLM scorer to compare against. Thank you.

**If `[WINDOW]` doesn't include April–May 2021**, swap the hook for one inside the window. Every row below is sourced in `key_events.csv`:

| Date (UTC) | Fact you can say | Source |
|---|---|---|
| 2021-02-04 | A burst of Musk posts promoting DOGE as "the people's crypto" sent it up more than 50% on the day | CNN |
| 2021-04-28 | Musk said he'd host SNL as "the Dogefather"; DOGE jumped about 20% | Newsweek |
| 2021-05-09 | On SNL (aired May 8, ET), Musk joked DOGE was "a hustle"; it fell as much as about 30% | CNBC |
| 2022-04-25 | Twitter's board accepted Musk's buyout; DOGE rose more than 20% that afternoon | CNBC |

## 4. The method for a non-technical judge (20 seconds)

> "It's a scored dictionary of about 220 crypto words and emoji. We add up a post's words, flip anything negated, and shrink
> anything hedged, like 'maybe'. Positive means up, negative means down, and the size is the conviction. We set it on
> `[TRAIN PERIOD]` and judged it on `[TEST PERIOD]`. The bar isn't 50%. It's what a blind guesser with the same mix of ups and downs would score."

| Piece | Plain English | Detail if asked |
|---|---|---|
| Keyword model | A dictionary with points: "to the moon" +3, "rug pull" −3.5, 🚀 +2.5 | `lexicons/sentiment_lexicon.csv`. Longest phrase wins, so "pump and dump" isn't scored as "pump". Rules follow VADER. |
| Direction + conviction | Sign of the score → UP/DOWN. Strength → LOW/MED/HIGH. A daily call combines all of that day's posts | Conviction = score strength × account influence × "clearly about the coin". If Musk-only, the influence factor is the same for every post. |
| Train/test split | Rules and cutoffs are set on the first part of `[WINDOW]`, then frozen and scored on the rest | Conviction cutoffs and learned keywords are fit on `[TRAIN PERIOD]` only |
| No-skill baseline | If DOGE rose on most days and you always said "up," you'd look smart by luck. This is the rate to beat | The hit rate expected if calls were independent of outcomes, given how often we said UP and how often price rose |

**One post, scored** (the project's own scorer, current lexicon; illustrative posts, not real ones):

| Post | Words matched (points) | Score, −1 to +1 | Call |
|---|---|---|---|
| "Dogecoin to the moon 🚀🚀" | to the moon +3.0, 🚀 +2.5, 🚀 +2.5 (total +8.0) | **+0.90** | UP, strong |
| "Maybe $DOGE to the moon?" | to the moon +3.0, then *maybe* and the `?` shrink it | **+0.44** | UP, weaker |
| "Not bullish on $DOGE. Looks like a pump and dump." | bullish −2.2 (negated), pump and dump −3.0 | **−0.80** | DOWN, strong |

Say it: *"'To the moon' is plus three and each rocket is plus two and a half, so it's strongly positive: an UP call. Add 'maybe' and a question mark, and the score roughly halves. It's still UP, but with lower conviction."*
Which bucket (LOW/MED/HIGH) a post lands in depends on cutoffs fit on `[TRAIN PERIOD]`, so don't name a bucket for these examples.
If the lexicon gets tuned, re-check them with `scorer.explain(...)` or notebook section 13.

## 5. Strong result vs. null result (both are fine)

`findings.md` tells you which case you're in. Look for its exact wording:

| Case | How you know | Slide 3 title | What to say |
|---|---|---|---|
| **Strong** | Headline says "distinguishable from chance" **and** the momentum check says "beat" | "Calls were right `[HIT RATE]` of the time vs. `[NO-SKILL RATE]` by chance" | "On data it never saw, the words beat chance by `[EDGE]` points." Then keep it modest: "a signal, not a strategy." |
| **Echo** | Beats no-skill, but the momentum check says "did **not** beat" | "The posts echoed price more than they led it" | "The words did better than chance, but no better than 'yesterday continues' (`[MOMENTUM RATE]`). The posts mostly follow the price." Use the event study on slide 4. |
| **Null** | Headline says "**not** distinguishable from chance" | "Even famous DOGE posts didn't beat chance on `[TEST PERIOD]`" | "Once you account for how often DOGE rises anyway, the words didn't reliably call the next day. That's worth knowing. Two possible reasons we can't separate yet: the reaction happens in minutes, or posts follow price." |

- If `findings.md` says "conviction did not clearly separate good calls from bad ones," say so in one clause and keep slide 3 on the main number.
- If `[N DAYS]` is small (likely if the set is Musk-only), say "with only `[N DAYS]` days, treat this as a pilot."
- With a null result, slides 3 and 4 stay the same and only the titles change. Don't apologize. A well-explained null beats an oversold result.

## 6. Three likely judge questions

| Question | Answer |
|---|---|
| "Isn't this just Elon?" | **10 accounts:** "Musk has the top influence weight (3.0 vs. 0.6–1.0 for the others), but every account is scored separately; the per-account table is in notebook section 7. Weight changes conviction, never direction." **Musk-only:** "Yes, by design. He's the account with documented price moves, and data for the others was thin. Adding them is next." |
| "How do you know it isn't overfit or luck?" | "Conviction cutoffs and learned keywords were fit on `[TRAIN PERIOD]` only. The word list was never tuned on `[TEST PERIOD]` posts and was frozen before the final run. We test against the no-skill rate, not 50%, with a binomial test over `[N DAYS]` daily calls (p = `[P VALUE]`)." *If pressed:* a few hand-picked terms (e.g. "hustle") were inspired by famous 2021 moments, which is why we also test a word list learned only from `[TRAIN PERIOD]`. |
| "Why keywords instead of ChatGPT or another LLM?" | "Explainability and speed. Every call lists the exact words behind it, so you can check any call in one sentence. An LLM scorer is the natural next comparison." |

More Q&A (trading, why the baseline isn't 50%) is in [`README.md`](README.md#qa-prep-likely-questions).

## 7. Don't

- **Don't oversell.** No "predicts," "alpha," or "beats the market." Even a strong result is "a confidence signal, not a trading bot."
- **Don't demo live.** Keep the notebook open in a tab for Q&A only.
- **Don't show tables.** One hero number with its baseline, or one chart.
- **Don't show a number without its baseline and n.** "`[HIT RATE]` vs. `[NO-SKILL RATE]`, n = `[N DAYS]`" always travel together.
- **Don't type numbers from memory.** Copy them from the latest `findings.md`.
- **Don't present anything marked SYNTHETIC DATA**, and don't use `05_signal_vs_buy_and_hold.png` as a trading claim.
- **Don't claim a "bear-market test".** The test is Sep–Dec 2021, a calmer market after the mania, not 2022.
- **Don't blur background and results.** The SNL moves are reported news, not model output.

## 8. Formatting: the four rules that matter

Everything else is in [`formatting_guide.md`](formatting_guide.md).

1. **Titles are takeaways.** A judge who reads only the five titles should get the whole story.
2. **One hero number per results slide**, 60pt or larger, with the baseline right beside it and `n` small underneath. Round to whole percentages.
3. **Use the exported PNGs as-is, one per slide**, cropped to the panel that matters. The color code is blue = UP/bullish, red = DOWN/bearish, gray = baseline/price, violet = the model's hit rate.
4. **No more than 15 words of body text per slide.** The script carries the detail.

## Last check before you walk on

- [ ] `findings.md` has no SYNTHETIC or Pending banner, and no chart has a watermark.
- [ ] Every bracket is filled from the **latest** `findings.md`, and `[TEST PERIOD]` matches `train_end` (see the label trap above).
- [ ] Slide 3 shows the result, the baseline, and `n`.
- [ ] Slides open offline, with charts embedded.
- [ ] Timed run-through at 1:50 or less. The first sentence is memorized.
