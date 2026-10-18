# Formatting guide for a 2-minute talk

In two minutes the audience remembers **one number and one picture**. Every formatting choice should protect those two things.

## Structure

- **5 slides at most**, about 20–25 seconds each. A slide you'd rush through is a slide to cut.
- **One idea per slide.** If a slide needs "and" in its title, split it or cut half.
- **Titles are takeaways, not topics.** Write "High-conviction calls were right [X]% of the time", not "Results".
  A judge who reads only the titles should get the whole story.
- Order: **hook → method in one picture → headline result → one supporting insight → caveat and next step.**

## Text

- **No more than 15 words of body text per slide.** The script carries the detail; the slide carries the point.
- No paragraphs, and no more than 3 bullets. Never read a slide aloud.
- Use plain words: "right 6 times out of 10", not "directional accuracy of 0.60". Define "conviction" once, out loud.
- Say **"out-of-sample"** or **"on 2022 data we never tuned on"**. It's the strongest credibility signal you have.

## Numbers

- **One hero number per results slide**, large (60pt or more), with its comparison right beside it: *"[X]% vs. [Y]% by chance"*.
  A number without its baseline means nothing.
- Round to whole percentages. Show `n` small underneath (*n = [days]*) so nobody wonders whether it's 5 days.
- Use the numbers in [`findings.md`](findings.md) exactly. Don't re-type them from memory.

## Charts

- **Use the exported PNGs from `figures/` as-is.** They share one visual language, and recoloring breaks it:

  | Color | Meaning |
  |---|---|
  | Blue | Bullish call / UP |
  | Red | Bearish call / DOWN |
  | Gray | No call / baselines / price |
  | Violet | The model's hit rate |

- **One chart per slide.** Crop to the panel that matters; the 1-day panel of the conviction chart is usually enough.
- If the slide title already says the takeaway, crop out the chart's own title so it doesn't repeat.
- Never use dual axes, 3D, or pie charts. Never show a table when a chart or a single number will do.
- Point at the one bar or line that matters. A simple arrow or a highlight box is enough.

## Typography and layout

- 16:9, a light background close to the chart surface (`#FCFCFB`) so the charts blend in rather than sitting in white boxes.
- One sans-serif font throughout. Titles 32–40pt, body text at least 24pt, nothing under 18pt.
- Left-align text. Keep the title in the same spot on every slide, with generous margins.
- High contrast: dark text on a light background. Don't use color alone to carry meaning; label it ("bullish", "bearish").

## Honesty (judges notice)

- Always show the baseline next to the result.
- If p ≥ 0.05, say "no reliable evidence", not "it predicts". A clean null result, well explained, beats an oversold one.
- Say one caveat out loud: daily prices blur a minutes-scale reaction, and keywords miss sarcasm and memes.
- Don't show the equity curve as a trading claim. If you use it, call it "illustrative, no trading costs".

## Delivery

- Rehearse with a timer. Aim for **1:50**.
- One speaker. Hand-offs cost about 5 seconds each.
- Don't demo the notebook live in a 2-minute slot. Keep it open in a tab for Q&A.
- Write the first sentence on a card and memorize it. A strong start fixes the pacing for the rest.

## Pre-flight checklist

- [ ] The notebook ran on **real data**: no "SYNTHETIC DATA" watermark on any chart, no warning banner in `findings.md`.
- [ ] Every number on a slide matches `findings.md` from the **latest** run.
- [ ] The headline slide shows the result, the baseline, and `n`.
- [ ] Slides open offline (charts embedded, not linked).
- [ ] Timed run-through at 1:50 or less.

## Slide skeleton

```
┌──────────────────────────────────────────────────────────────┐
│  High-conviction calls were right [X]% of the time           │  ← takeaway title, 36pt
│                                                              │
│      [X]%         vs.   [Y]%                                 │  ← hero number + baseline, 72pt / 40pt
│      high-conviction    no-skill                             │
│      n = [days], 2022 (out-of-sample)                        │  ← 18pt, muted
│                                                              │
│      [ 02_hit_rate_by_conviction.png: 1-day panel ]          │
└──────────────────────────────────────────────────────────────┘
```
