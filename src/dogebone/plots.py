"""Presentation-ready matplotlib charts. Polarity uses a diverging blue (bullish) / red (bearish) pair."""

from __future__ import annotations

import textwrap
import unicodedata
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter, LogLocator, PercentFormatter

SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
UP, DOWN, NEUTRAL = "#2a78d6", "#e34948", "#898781"
ACCENT = "#6250d6"  # model accuracy (not a polarity)
DIR_COLORS = {"UP": UP, "DOWN": DOWN, "NEUTRAL": NEUTRAL}
DIR_LABELS = {"UP": "Bullish call", "DOWN": "Bearish call", "NEUTRAL": "No call"}
# Matplotlib can't draw color emoji on most systems, so chart labels spell them out.
EMOJI_NAMES = {
    "🚀": "[rocket]", "🌕": "[full moon]", "🌙": "[moon]", "📈": "[chart up]", "📉": "[chart down]", "💎": "[diamond]",
    "🙌": "[hands]", "🔥": "[fire]", "🐕": "[dog]", "🐶": "[dog face]", "🔴": "[red dot]", "🟢": "[green dot]",
    "🤡": "[clown]", "💩": "[poop]", "💰": "[money bag]", "🤑": "[money face]", "🩸": "[blood]", "⚠": "[warning]",
    "✅": "[check]", "❌": "[cross]",
}


def label(term: str) -> str:
    out = []
    for ch in str(term):
        if ch in EMOJI_NAMES:
            out.append(EMOJI_NAMES[ch])
        elif ord(ch) > 0x2600 and not ch.isalnum():
            out.append(f"[{unicodedata.name(ch, 'emoji').lower()}]")
        else:
            out.append(ch)
    return "".join(out)


def use_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
            "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlecolor": INK,
            "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
            "axes.labelsize": 10, "axes.spines.top": False, "axes.spines.right": False,
            "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
            "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 9, "ytick.labelsize": 9,
            "legend.frameon": False, "legend.fontsize": 9, "legend.labelcolor": INK2,
            "lines.linewidth": 2, "lines.solid_capstyle": "round", "lines.solid_joinstyle": "round",
            "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"], "figure.dpi": 110,
        }
    )


def save(fig, name: str, *dirs: Path, watermark: str | None = None) -> list[Path]:
    if watermark:
        fig.text(0.5, 0.5, watermark, fontsize=44, color=MUTED, alpha=0.18, rotation=18,
                 ha="center", va="center", fontweight="bold", zorder=10)
    paths = []
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{name}.png"
        fig.savefig(p, dpi=200, bbox_inches="tight")
        paths.append(p)
    return paths


def _usd(v, _=None) -> str:
    return f"${v:.2f}" if v >= 0.1 else f"${v:.3g}"


def price_with_signals(returns: pd.DataFrame, daily: pd.DataFrame, events: pd.DataFrame, start, end,
                       max_events: int = 8, buckets=("HIGH",)):
    fig, ax = plt.subplots(figsize=(12, 5))
    px = returns.loc[start:end, "close"]
    ax.plot(px.index, px.values, color=INK2, linewidth=1.6, label="DOGE close (USD)")
    d = daily[(daily["anchor_date"] >= pd.Timestamp(start)) & (daily["anchor_date"] <= pd.Timestamp(end))]
    if buckets and "conviction_bucket" in d:
        d = d[d["conviction_bucket"].isin(buckets)]
    d = d[d["direction"] != "NEUTRAL"].drop(columns="close", errors="ignore")
    d = d.merge(returns[["close"]], left_on="anchor_date", right_index=True)
    for dir_, color in [("UP", UP), ("DOWN", DOWN)]:
        s = d[d["direction"] == dir_]
        ax.scatter(s["anchor_date"], s["close"], s=20 + 120 * s["conviction"], color=color, edgecolor=SURFACE,
                   linewidth=1.5, alpha=0.85, zorder=3, label=DIR_LABELS[dir_])
    ev = events[(events["date"] >= pd.Timestamp(start)) & (events["date"] <= pd.Timestamp(end))]
    if "on_chart" in ev:  # curated headline events keep labels readable
        ev = ev[ev["on_chart"] == 1]
    ev = ev.head(max_events)
    # Numbered event markers with a key underneath: long rotated labels collide when events cluster.
    prev, stagger = None, 0
    for k, (_, e) in enumerate(ev.iterrows(), 1):
        ax.axvline(e["date"], color=AXIS, linewidth=1, zorder=1)
        stagger = (stagger + 1) % 2 if prev is not None and (e["date"] - prev).days < 25 else 0
        ax.annotate(str(k), xy=(e["date"], 1.0), xycoords=("data", "axes fraction"), xytext=(0, -3 - 15 * stagger),
                    textcoords="offset points", ha="center", va="top", fontsize=7.5, color=INK2,
                    bbox=dict(boxstyle="circle,pad=0.25", fc=SURFACE, ec=AXIS, lw=0.8), zorder=4)
        prev = e["date"]
    if len(ev):
        # Non-breaking spaces inside each label so wrapping only happens between labels.
        key = "    ".join(f"({k}) {e['label']}".replace(" ", " ") for k, (_, e) in enumerate(ev.iterrows(), 1))
        fig.text(0.01, -0.01, textwrap.fill(key, 190), fontsize=8, color=MUTED, ha="left", va="top")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(_usd))
    ax.yaxis.set_minor_locator(LogLocator(base=10, subs=(2, 5)))  # label 2x and 5x only; full minors collide
    ax.yaxis.set_minor_formatter(FuncFormatter(_usd))
    which = " / ".join(b.lower() for b in buckets) + "-conviction" if buckets else "all"
    ax.set_title(f"DOGE price with {which} daily post-sentiment calls (marker size = conviction)", pad=28)
    ax.set_ylabel("Close, log scale")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, borderaxespad=0.2)
    fig.tight_layout()
    return fig


def hit_rate_by_conviction(table: pd.DataFrame, title: str = "Hit rate by conviction"):
    """table: rows per (conviction_bucket, horizon_d) with hit_rate, null_hit_rate, n_calls."""
    horizons = sorted(table["horizon_d"].unique())
    fig, axes = plt.subplots(1, len(horizons), figsize=(4 * len(horizons), 3.8), sharey=True, squeeze=False)
    order = [c for c in ["LOW", "MEDIUM", "HIGH"] if c in set(table["conviction_bucket"])]
    for ax, h in zip(axes[0], horizons):
        t = table[table["horizon_d"] == h].set_index("conviction_bucket").reindex(order)
        x = range(len(order))
        ax.bar(x, t["hit_rate"], width=0.5, color=ACCENT, zorder=2, label="Sentiment calls")
        null = t["null_hit_rate"].mean()
        ax.axhline(null, color=INK2, linewidth=1.2, zorder=3, label=f"No-skill rate ({null:.0%})")
        for xi, hr in enumerate(t["hit_rate"]):
            if pd.notna(hr):
                ax.text(xi, max(hr, null) + 0.02, f"{hr:.0%}", ha="center", va="bottom", fontsize=9, color=INK)
        ax.set_xticks(list(x), [f"{o.title()}\nn={int(n) if pd.notna(n) else 0}" for o, n in zip(order, t["n_calls"])])
        ax.legend(loc="upper left", fontsize=8)
        ax.set_title(f"{h}-day horizon", fontsize=11)
        ax.set_ylim(0, 1)
        ax.yaxis.set_major_formatter(PercentFormatter(1.0))
        ax.grid(axis="x", visible=False)
    axes[0][0].set_ylabel("Directional hit rate")
    fig.suptitle(title, x=0.01, ha="left", fontsize=13, fontweight="bold", color=INK)
    fig.tight_layout()
    return fig


def event_study(paths: pd.DataFrame, title: str = "Average DOGE path around posts"):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for grp in ["UP", "NEUTRAL", "DOWN"]:
        p = paths[paths["group"] == grp]
        if p.empty:
            continue
        c = DIR_COLORS[grp]
        ax.plot(p["day"], p["mean"], color=c, label=f"{DIR_LABELS[grp]} (n={int(p['n'].max())})")
        ax.fill_between(p["day"], p["mean"] - p["sem"], p["mean"] + p["sem"], color=c, alpha=0.1, linewidth=0)
        last = p.iloc[-1]
        ax.text(last["day"] + 0.2, last["mean"], f"{last['mean']:+.1%}", va="center", fontsize=8.5, color=INK2)
    ax.axvline(0, color=AXIS, linewidth=1)
    ax.axhline(0, color=AXIS, linewidth=1)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_xlabel("Days from anchor close (0 = daily close nearest the post)")
    ax.set_ylabel("Cumulative return")
    ax.set_title(title)
    ax.legend(loc="upper left")
    fig.tight_layout()
    return fig


def keyword_bars(stats: pd.DataFrame, top: int = 10, title: str = "Keywords that preceded moves (training period)"):
    s = pd.concat([stats[stats["z"] > 0].nlargest(top, "z"), stats[stats["z"] < 0].nsmallest(top, "z")])
    s = s.sort_values("log_odds")
    fig, ax = plt.subplots(figsize=(8, 0.32 * len(s) + 1.2))
    colors = [UP if v > 0 else DOWN for v in s["log_odds"]]
    names = [f"{label(t)}  (n={int(n)})" for t, n in zip(s["term"], s["n"])]
    ax.barh(names, s["log_odds"], height=0.6, color=colors, zorder=2)
    ax.axvline(0, color=AXIS, linewidth=1)
    ax.set_xlabel("Log-odds of next move being UP vs. base rate  (blue = bullish, red = bearish)")
    ax.set_title(title)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return fig


def equity_curves(eq: pd.DataFrame, title: str = "Illustrative: following the daily call (1-day hold, no costs)"):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(eq.index, eq["buy_and_hold"], color=INK2, linewidth=1.6, label="Buy & hold DOGE")
    ax.plot(eq.index, eq["follow_signal"], color=ACCENT, label="Follow post-sentiment call")
    for col in ["buy_and_hold", "follow_signal"]:
        ax.text(eq.index[-1], eq[col].iloc[-1], f"  {eq[col].iloc[-1]:.2f}x", va="center", fontsize=8.5, color=INK2)
    ax.axhline(1, color=AXIS, linewidth=1)
    ax.set_ylabel("Growth of $1")
    ax.set_title(title)
    ax.legend(loc="upper left")
    fig.tight_layout()
    return fig


# --- Trained model (notebooks/02_direction_model.ipynb) ---------------------------------------------------------


def model_vs_baselines(table: pd.DataFrame, title: str = "Model hit rate vs. baselines (out-of-sample)"):
    """table: one row per horizon with n, hit_rate, null_hit_rate, majority_hit_rate, momentum_hit_rate."""
    t = table.sort_values("horizon_d").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    width = 0.24
    series = [("hit_rate", "Model", ACCENT), ("majority_hit_rate", "Always the training majority", MUTED),
              ("momentum_hit_rate", "Momentum (last move continues)", AXIS)]
    for j, (col, name, color) in enumerate(series):
        xs = [i + (j - 1) * (width + 0.03) for i in range(len(t))]
        ax.bar(xs, t[col], width=width, color=color, zorder=2, label=name)
        if col == "hit_rate":  # label above the no-skill line too, so the two never collide
            for x, v, null in zip(xs, t[col], t["null_hit_rate"]):
                ax.text(x, max(v, null) + 0.02, f"{v:.0%}", ha="center", va="bottom", fontsize=9, color=INK,
                        fontweight="bold")
    for i, null in enumerate(t["null_hit_rate"]):
        ax.hlines(null, i - 0.42, i + 0.42, color=INK, linewidth=1.4, zorder=3,
                  label="No-skill rate" if i == 0 else None)
    ax.set_xticks(range(len(t)), [f"{h}-day horizon\nn = {n} post days" for h, n in zip(t["horizon_d"], t["n"])])
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylabel("Directional hit rate")
    ax.grid(axis="x", visible=False)
    ax.set_title(title, pad=30)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=4, borderaxespad=0.2, fontsize=8)
    fig.tight_layout()
    return fig


def model_coefficients(coef: pd.DataFrame, title: str = "What the model learned"):
    """coef: DirectionModel.coefficients() -> label, coef_per_sd."""
    c = coef.sort_values("coef_per_sd")
    fig, ax = plt.subplots(figsize=(8, 0.38 * len(c) + 1.3))
    ax.barh(c["label"], c["coef_per_sd"], height=0.6, color=[UP if v > 0 else DOWN for v in c["coef_per_sd"]], zorder=2)
    ax.axvline(0, color=AXIS, linewidth=1)
    for y, v in enumerate(c["coef_per_sd"]):
        ax.text(v + (0.01 if v >= 0 else -0.01), y, f"{v:+.2f}", va="center", ha="left" if v >= 0 else "right",
                fontsize=8.5, color=INK2)
    lim = max(0.1, c["coef_per_sd"].abs().max() * 1.35)
    ax.set_xlim(-lim, lim)
    ax.set_xlabel("Push on the log-odds of UP per 1 SD of the feature  (blue = toward UP, red = toward DOWN)")
    fig.suptitle(title, x=0.01, ha="left", fontsize=13, fontweight="bold", color=INK)  # long y labels: align to figure
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return fig


def model_calls_timeline(returns: pd.DataFrame, preds: pd.DataFrame, start, end,
                         title: str = "Model calls on the held-out months"):
    """Price line with one marker per post day: triangle up/down = call, filled = right, hollow = wrong."""
    fig, ax = plt.subplots(figsize=(11, 4.4))
    px = returns.loc[start:end, "close"]
    ax.plot(px.index, px.values, color=INK2, linewidth=1.6, label="DOGE close (USD)", zorder=1)
    d = preds[preds["actual"].notna()]
    for dir_, marker, color in [("UP", "^", UP), ("DOWN", "v", DOWN)]:
        for hit, face, word in [(True, color, "right"), (False, SURFACE, "wrong")]:
            s = d[(d["direction"] == dir_) & (d["hit"] == hit)]
            if s.empty:
                continue
            ax.scatter(s["anchor_date"], s["close"], s=60 + 140 * s["conviction"], marker=marker, facecolor=face,
                       edgecolor=color, linewidth=1.8, zorder=3, label=f"{DIR_LABELS[dir_].split()[0]} call, {word}")
    ax.yaxis.set_major_formatter(FuncFormatter(_usd))
    ax.set_ylabel("Close")
    ax.set_title(title, pad=28)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=5, borderaxespad=0.2, fontsize=8.5)
    fig.tight_layout()
    return fig
