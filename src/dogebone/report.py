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
    daily_by_conviction: pd.DataFrame,
    posts_by_account: pd.DataFrame,
    learned_vs_lexicon: pd.DataFrame,
    term_table: pd.DataFrame,
    n_posts: int,
    n_accounts: int,
    figures: list[str],
    attention: pd.DataFrame | None = None,
    coverage: dict | None = None,
) -> str:
    test_start = pd.Timestamp(cfg.train_end) + pd.Timedelta(days=1)
    train_label = f"the {pd.Timestamp(cfg.analysis_start):%b %Y}–{pd.Timestamp(cfg.train_end):%b %Y} calibration period"
    test_label = f"out-of-sample {test_start:%b}–{pd.Timestamp(cfg.analysis_end):%b %Y} data"
    full_label = (f"the full window ({pd.Timestamp(cfg.analysis_start):%b}–{pd.Timestamp(cfg.analysis_end):%b %Y}; "
                  "the hand-crafted lexicon has no parameters fit to this data)")
    test = _row(daily_by_period, period="test", horizon_d=focus_h)
    train = _row(daily_by_period, period="train", horizon_d=focus_h)
    full = _row(daily_by_period, period="all", horizon_d=focus_h)
    # Too few out-of-sample days to say anything: lead with the full window and show the test slice beside it.
    use_full = full is not None and (test is None or test["n_calls"] < cfg.min_test_days)
    head, head_label, head_period = (full, full_label, "all") if use_full else (test, test_label, "test")

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
    if head is not None:
        lines.append(f"- {headline_sentence(head, focus_h, head_label)}")
    for row, label in [(train, train_label), (test, test_label)]:
        if row is not None and row is not head:
            lines.append(
                f"- Split view, {label}: {_pct(row['hit_rate'])} vs. {_pct(row['null_hit_rate'])} no-skill "
                f"(n = {int(row['n_calls'])} days{'; too few to conclude' if row['n_calls'] < cfg.min_test_days else ''})."
            )
    lines += ["", "## Supporting findings (pick 2 for the slides)", ""]

    if coverage:
        lines.append(
            f"- **Coverage:** only {coverage['posts_with_terms']} of {coverage['posts']} posts "
            f"({coverage['posts_with_terms'] / max(coverage['posts'], 1):.0%}) contained a sentiment keyword, so only "
            f"{coverage['called_days']} of {coverage['post_days']} post days got a call. Most DOGE posts here are terse "
            "(a bare 'Doge', an emoji, a meme)."
        )
    if attention is not None and not attention.empty:
        a = attention[attention["horizon_d"] == focus_h]
        if not a.empty:
            a = a.iloc[0]
            sig = "significant" if a["p_value"] < 0.05 else "not significant"
            lines.append(
                f"- **Attention vs. words:** regardless of wording, DOGE rose over the next {focus_h}d after "
                f"**{_pct(a['up_rate_post_days'])}** of post days vs. **{_pct(a['up_rate_all_days'])}** of all days "
                f"(mean {a['mean_ret_post_days']:+.2%} vs. {a['mean_ret_all_days']:+.2%}; n = {int(a['n_post_days'])} days, "
                f"p = {a['p_value']:.3f}, {sig})."
            )

    if head is not None:
        mom = head["momentum_hit_rate"]
        beat = "beat" if head["hit_rate"] > mom else "did **not** beat"
        lines.append(
            f"- **Momentum check:** sentiment {beat} a simple 'yesterday's direction continues' rule "
            f"({_pct(head['hit_rate'])} vs. {_pct(mom)}). If it didn't, posts are mostly *echoing* price, not leading it."
        )
        lines.append(
            f"- **Magnitude:** after bullish calls DOGE averaged {head['mean_ret_when_up']:+.2%} over {focus_h}d; after bearish calls "
            f"{head['mean_ret_when_down']:+.2%} (spread {head['spread_pp']:+.1f} pp)."
        )

    hz = daily_by_period[daily_by_period["period"] == head_period].sort_values("horizon_d")
    if len(hz) > 1:
        lines.append(
            f"- **Horizon decay:** hit rate by horizon ({'full window' if use_full else 'test data'}): "
            + ", ".join(f"{int(r.horizon_d)}d {_pct(r.hit_rate)}" for r in hz.itertuples())
            + "."
        )

    conv = daily_by_conviction[daily_by_conviction["horizon_d"] == focus_h].set_index("conviction_bucket")
    if {"HIGH", "LOW"} <= set(conv.index):
        hi, lo = conv.loc["HIGH", "hit_rate"], conv.loc["LOW", "hit_rate"]
        n_hi, n_lo = int(conv.loc["HIGH", "n_calls"]), int(conv.loc["LOW", "n_calls"])
        if min(n_hi, n_lo) < 15:
            informative = "too few days per bucket to judge conviction"
        elif hi - lo >= 0.05:
            informative = "conviction looks informative"
        else:
            informative = "conviction did not clearly separate good calls from bad ones"
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
            f"- **Hand-crafted vs. learned keywords (test):** {_pct(lv.loc['hand-crafted lexicon', 'hit_rate'])} "
            f"(n={int(lv.loc['hand-crafted lexicon', 'n_calls'])}) vs. "
            f"{_pct(lv.loc['learned keywords', 'hit_rate'])} (n={int(lv.loc['learned keywords', 'n_calls'])}). Learned keywords were fit on {train_label[4:]} only."
        )

    if not term_table.empty:
        bull = ", ".join(f"`{t}`" for t in term_table[term_table["z"] > 0].nlargest(5, "z")["term"]) or "none"
        bear = ", ".join(f"`{t}`" for t in term_table[term_table["z"] < 0].nsmallest(5, "z")["term"]) or "none"
        lines.append(
            f"- **Keywords that preceded up-moves:** {bull}. **Down-moves:** {bear}. "
            f"(Training period, at least {cfg.min_term_count} posts per term; exploratory.)"
        )

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


def _model_sentence(m: pd.Series, h: int, label: str) -> str:
    verdict = "distinguishable from chance" if m["p_value"] < 0.05 else "**not** distinguishable from chance"
    return (
        f"{label}: the model called the next-{h}-day direction right **{_pct(m['hit_rate'])}** of the time vs. "
        f"**{_pct(m['null_hit_rate'])}** no-skill ({m['edge_pp']:+.1f} pp, p = {m['p_value']:.3f}, n = {int(m['n'])} post days; "
        f"AUC {m['auc']:.2f}, Brier skill {m['brier_skill']:+.2f}): {verdict}."
    )


def _cell(s, width: int = 70) -> str:
    s = " ".join(str(s).split()).replace("|", "/")
    return s if len(s) <= width else s[: width - 1] + "…"


def write_model_findings(
    path: Path,
    cfg: Config,
    data_mode: str,
    focus_h: int,
    walk_forward: pd.DataFrame,
    holdout: pd.DataFrame,
    permutation: pd.DataFrame,
    conviction: pd.DataFrame,
    coefficients: pd.DataFrame,
    test_preds: pd.DataFrame,
    n_events: int,
    n_posts: int,
    figures: list[str],
    l2: float,
    wf_window: str,
    skipped_months: list | None = None,
) -> str:
    """Draft presentation/model_findings.md from notebooks/02_direction_model.ipynb results."""
    full = "text + market"
    test_start = pd.Timestamp(cfg.train_end) + pd.Timedelta(days=1)
    wf_label = f"Walk-forward ({wf_window}, refit monthly on earlier months only)"
    ho_label = f"Held-out {test_start:%b}–{pd.Timestamp(cfg.analysis_end):%b %Y} (trained on {pd.Timestamp(cfg.analysis_start):%b}–{pd.Timestamp(cfg.train_end):%b} only)"
    wf_head = _row(walk_forward, features=full, horizon_d=focus_h)
    ho_head = _row(holdout, features=full, horizon_d=focus_h)

    lines = []
    if data_mode != "raw":
        lines += ["> ## ⚠️ SYNTHETIC DATA: DO NOT PRESENT", "> These numbers come from `data/sample/`.", ""]
    lines += [
        "# Model findings (auto-drafted by notebooks/02_direction_model.ipynb)",
        "",
        f"_Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC from {n_posts} @elonmusk DOGE posts on {n_events} post days, "
        f"{cfg.analysis_start} to {cfg.analysis_end}. Model: L2 logistic regression (penalty {l2:g}, fixed in advance) on "
        f"post-day text and market features. Focus horizon: {focus_h} day(s), chosen before testing._",
        "",
        "## Headline",
        "",
    ]
    for row, label in [(wf_head, wf_label), (ho_head, ho_label)]:
        if row is not None and row["n"]:
            lines.append(f"- {_model_sentence(row, focus_h, label)}")
    if wf_head is not None and wf_head["n"]:
        beat_mom = "beat" if wf_head["hit_rate"] > wf_head["momentum_hit_rate"] else "did **not** beat"
        beat_maj = "beat" if wf_head["hit_rate"] > wf_head["majority_hit_rate"] else "did **not** beat"
        lines.append(
            f"- Against simple rules (walk-forward, {focus_h}d): the model {beat_maj} always calling the training majority "
            f"({_pct(wf_head['majority_hit_rate'])}) and {beat_mom} momentum ({_pct(wf_head['momentum_hit_rate'])})."
        )

    if skipped_months:
        lines.append(f"- Walk-forward months skipped for too little history: {', '.join(skipped_months)}.")
    lines += ["", "## Every horizon (text + market features)", "",
              "| Test | Horizon | n | Model | No-skill | p | Majority rule | Momentum | AUC | Brier skill |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for name, table in [("walk-forward", walk_forward), ("held-out", holdout)]:
        for r in table[table["features"] == full].sort_values("horizon_d").itertuples():
            lines.append(
                f"| {name} | {r.horizon_d}d | {r.n} | {_pct(r.hit_rate)} | {_pct(r.null_hit_rate)} | {r.p_value:.3f} | "
                f"{_pct(r.majority_hit_rate)} | {_pct(r.momentum_hit_rate)} | {r.auc:.2f} | {r.brier_skill:+.2f} |"
            )
    n_tests = len(walk_forward[walk_forward["features"] == full])
    lines += ["", f"_Three horizons were tested, so a single p below 0.05 is weak evidence: the Bonferroni bar is "
              f"{0.05 / max(n_tests, 1):.3f}. A Brier skill above 0 means the probabilities beat the training base rate._", ""]

    lines += ["## Is it the words or the market? (walk-forward)", "",
              "| Features | " + " | ".join(f"{h}d hit / AUC" for h in sorted(walk_forward["horizon_d"].unique())) + " |",
              "|---|" + "---|" * walk_forward["horizon_d"].nunique()]
    for name, g in walk_forward.groupby("features", sort=False):
        cells = [f"{_pct(r.hit_rate)} / {r.auc:.2f}" for r in g.sort_values("horizon_d").itertuples()]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines.append("")
    if permutation is not None and not permutation.empty:
        lines += ["**Permutation tests** (walk-forward, text + market; p = share of shuffled runs at least as good):", ""]
        for r in permutation.sort_values(["shuffle", "horizon_d"]).itertuples():
            what = "outcomes shuffled (are any features informative?)" if r.shuffle == "outcome" else \
                "Musk's text features shuffled, market kept (do the words add anything?)"
            lines.append(f"- {r.horizon_d}d, {what}: hit-rate p = {r.p_hit_rate:.3f}, AUC p = {r.p_auc:.3f} "
                         f"({r.n_perm} shuffles).")
        lines.append("")

    if conviction is not None and not conviction.empty:
        lines += [f"## Does conviction mean anything? (walk-forward, {focus_h}d)", "",
                  "| Conviction | n | Mean P(up) | Realized up-rate | Hit rate |", "|---|---|---|---|---|"]
        for r in conviction.itertuples():
            lines.append(f"| {r.conviction_bucket} | {r.n} | {_pct(r.mean_p_up)} | {_pct(r.realized_up_rate)} | {_pct(r.hit_rate)} |")
        lines += ["", "_HIGH = the model is at least 70% sure either way; LOW = between 40% and 60%._", ""]

    if coefficients is not None and not coefficients.empty:
        lines += [f"## What the final {focus_h}d model learned (fit on all of {pd.Timestamp(cfg.analysis_start):%Y})", ""]
        for r in coefficients.head(5).itertuples():
            lines.append(f"- {r.label}: {r.coef_per_sd:+.2f} log-odds per SD ({'toward UP' if r.coef_per_sd > 0 else 'toward DOWN'}).")
        lines.append("")

    if test_preds is not None and not test_preds.empty:
        lines += [f"## The held-out test, post day by post day ({focus_h}d)", "",
                  "| Anchor close | First post that day | P(up) | Call | Conviction | Actual | |", "|---|---|---|---|---|---|---|"]
        for r in test_preds.sort_values("anchor_date").itertuples():
            mark = "" if r.actual is None else ("✅" if r.hit == 1 else "❌")
            lines.append(f"| {r.anchor_date:%Y-%m-%d} | {_cell(str(r.texts).split(' | ')[0])} | {r.p_up:.0%} | {r.direction} | "
                         f"{r.conviction_bucket} | {r.actual or 'n/a'} | {mark} |")
        lines.append("")

    lines += [
        "## Caveats to say out loud",
        "",
        "- One account, one year: about 50 out-of-sample post days per horizon, so a 10-point edge is within noise.",
        "- 2021 changed regime (mania to slow bleed). Relationships learned in Feb–May can flip by the autumn.",
        "- Daily closes blur a minutes-scale reaction; posts are anchored to the nearest close (at most 12h of overlap).",
        "- Features and the penalty were fixed before testing; nothing was tuned on the test months.",
        "",
        "## Figures exported for slides",
        "",
        *[f"- `{f}`" for f in figures],
        "",
    ]
    md = "\n".join(lines)
    Path(path).write_text(md, encoding="utf-8")
    return md
