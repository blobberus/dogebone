"""Draft presentation/findings.md from notebook results so the slide numbers always match the analysis."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .config import Config


def _pct(x) -> str:
    return "n/a" if pd.isna(x) else f"{x:.0%}"


def _row(table: pd.DataFrame, **filters) -> pd.Series | None:
    t = table
    for k, v in filters.items():
        t = t[t[k] == v]
    return None if t.empty else t.iloc[0]


def headline_sentence(m: pd.Series, h: int, period_label: str) -> str:
    verdict = "distinguishable from chance" if m["p_value"] < 0.05 else "**not** distinguishable from chance"
    return (
        f"On {period_label}, daily post-sentiment calls got the next-{h}-day DOGE direction right "
        f"**{_pct(m['hit_rate'])}** of the time vs. **{_pct(m['null_hit_rate'])}** no-skill "
        f"({m['edge_pp']:+.1f} pp, p = {m['p_value']:.3f}, n = {int(m['n_calls'])} days): {verdict}."
    )


def write_findings(
    path: Path,
    cfg: Config,
    data_mode: str,
    focus_h: int,
    daily_by_period: pd.DataFrame,
    daily_by_conviction_test: pd.DataFrame,
    posts_by_account: pd.DataFrame,
    learned_vs_lexicon: pd.DataFrame,
    term_table: pd.DataFrame,
    n_posts: int,
    n_accounts: int,
    figures: list[str],
) -> str:
    train_label = f"the {cfg.analysis_start[:4]} calibration period"
    test_label = f"out-of-sample {pd.Timestamp(cfg.train_end).year + 1} data"
    test = _row(daily_by_period, period="test", horizon_d=focus_h)
    train = _row(daily_by_period, period="train", horizon_d=focus_h)

    lines = []
    if data_mode != "raw":
        lines += [
            "> ## ⚠️ SYNTHETIC DATA: DO NOT PRESENT",
            "> These numbers come from `data/sample/` (generated, with a planted signal).",
            "> Drop the real files into `data/raw/` and re-run the notebook.",
            "",
        ]
    lines += [
        "# Findings (auto-drafted by the notebook)",
        "",
        f"_Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC from {n_posts:,} posts by {n_accounts} accounts, "
        f"{cfg.analysis_start} to {cfg.analysis_end}. Focus horizon: {focus_h} day(s). "
        "Edit the wording before presenting, but keep the numbers in sync with the notebook._",
        "",
        "## Headline (use this as the slide-3 title)",
        "",
    ]
    if test is not None:
        lines.append(f"- {headline_sentence(test, focus_h, test_label)}")
    if train is not None:
        lines.append(f"- For comparison, {train_label}: {_pct(train['hit_rate'])} vs. {_pct(train['null_hit_rate'])} no-skill.")
    lines += ["", "## Supporting findings (pick 2 for the slides)", ""]

    if test is not None:
        mom = test["momentum_hit_rate"]
        beat = "beat" if test["hit_rate"] > mom else "did **not** beat"
        lines.append(
            f"- **Momentum check:** sentiment {beat} a simple 'yesterday's direction continues' rule "
            f"({_pct(test['hit_rate'])} vs. {_pct(mom)}). If it didn't, posts are mostly *echoing* price, not leading it."
        )
        lines.append(
            f"- **Magnitude:** after bullish calls DOGE averaged {test['mean_ret_when_up']:+.2%} over {focus_h}d; after bearish calls "
            f"{test['mean_ret_when_down']:+.2%} (spread {test['spread_pp']:+.1f} pp)."
        )

    hz = daily_by_period[daily_by_period["period"] == "test"].sort_values("horizon_d")
    if len(hz) > 1:
        lines.append(
            "- **Horizon decay:** hit rate by horizon on test data: "
            + ", ".join(f"{int(r.horizon_d)}d {_pct(r.hit_rate)}" for r in hz.itertuples())
            + "."
        )

    conv = daily_by_conviction_test[daily_by_conviction_test["horizon_d"] == focus_h].set_index("conviction_bucket")
    if {"HIGH", "LOW"} <= set(conv.index):
        hi, lo = conv.loc["HIGH", "hit_rate"], conv.loc["LOW", "hit_rate"]
        n_hi, n_lo = int(conv.loc["HIGH", "n_calls"]), int(conv.loc["LOW", "n_calls"])
        informative = (
            "conviction looks informative" if hi - lo >= 0.05
            else "conviction did not clearly separate good calls from bad ones"
        )
        lines.append(
            f"- **Conviction:** high-conviction days hit {_pct(hi)} (n={n_hi}) vs. low-conviction {_pct(lo)} (n={n_lo}), "
            f"so {informative}."
        )

    acc = posts_by_account[(posts_by_account["horizon_d"] == focus_h) & (posts_by_account["n_calls"] >= 30)]
    if not acc.empty:
        best = acc.sort_values("edge_pp", ascending=False).iloc[0]
        worst = acc.sort_values("edge_pp").iloc[0]
        lines.append(
            f"- **Accounts:** most predictive @{best['username']} ({_pct(best['hit_rate'])}, {best['edge_pp']:+.1f} pp, "
            f"n={int(best['n_calls'])}); least @{worst['username']} ({_pct(worst['hit_rate'])}, {worst['edge_pp']:+.1f} pp)."
        )

    lv = learned_vs_lexicon[learned_vs_lexicon["horizon_d"] == focus_h].set_index("method")
    if {"hand-crafted lexicon", "learned keywords"} <= set(lv.index):
        lines.append(
            f"- **Hand-crafted vs. learned keywords (test):** {_pct(lv.loc['hand-crafted lexicon', 'hit_rate'])} vs. "
            f"{_pct(lv.loc['learned keywords', 'hit_rate'])}. Learned keywords were fit on {cfg.analysis_start[:4]} only."
        )

    if not term_table.empty:
        bull = ", ".join(f"`{t}`" for t in term_table.nlargest(5, "z")["term"])
        bear = ", ".join(f"`{t}`" for t in term_table.nsmallest(5, "z")["term"])
        lines.append(f"- **Keywords that preceded up-moves:** {bull}. **Down-moves:** {bear}.")

    lines += [
        "",
        "## Caveats to say out loud (pick 1)",
        "",
        "- Daily prices can't isolate a post's minutes-scale impact; we anchor to the nearest daily close (at most 12h of overlap).",
        "- Overlapping multi-day windows and same-day posts inflate significance; daily aggregation reduces but doesn't remove this.",
        "- Lexicons miss sarcasm and memes (a large share of DOGE posts). Direction only, not price targets.",
        "",
        "## Figures exported for slides",
        "",
        *[f"- `{f}`" for f in figures],
        "",
    ]
    md = "\n".join(lines)
    Path(path).write_text(md, encoding="utf-8")
    return md
