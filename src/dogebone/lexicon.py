"""Explainable keyword/lexicon sentiment scorer for crypto posts (VADER-style rules, crypto vocabulary)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pandas as pd

from .config import Config
from .text import normalize, tokenize


@dataclass
class ScoreResult:
    sentiment: float  # in [-1, 1]
    raw: float
    hedge: float
    hits: list = field(default_factory=list)  # [(term, contribution)]

    @property
    def matched_terms(self) -> str:
        return ", ".join(f"{t}({c:+.1f})" for t, c in self.hits)


class LexiconScorer:
    def __init__(self, cfg: Config, lexicon: pd.DataFrame | None = None):
        self.cfg = cfg
        lex = lexicon if lexicon is not None else pd.read_csv(cfg.lexicon_dir / "sentiment_lexicon.csv")
        lex = lex.assign(term=lex["term"].str.lower().str.strip())
        self.weights = dict(zip(lex["term"], lex["weight"].astype(float)))
        self.max_ngram = max(len(t.split()) for t in self.weights)
        mods = pd.read_csv(cfg.lexicon_dir / "modifiers.csv")
        by_type = {k: dict(zip(g["term"], g["factor"].astype(float))) for k, g in mods.groupby("type")}
        self.negators = by_type.get("negator", {})
        self.intensifiers = {**by_type.get("intensifier", {}), **by_type.get("diminisher", {})}
        self.hedges = by_type.get("hedge", {})

    def score(self, text: str) -> ScoreResult:
        cfg = self.cfg
        toks = tokenize(text)
        words = [t for t, _ in toks]
        # Caps emphasis only counts when the rest of the post isn't also in caps (VADER rule).
        alpha_caps = [caps for tok, caps in toks if any(ch.isalpha() for ch in tok)]
        text_is_shouting = len(alpha_caps) >= 3 and all(alpha_caps)
        hits, raw, i = [], 0.0, 0
        while i < len(words):
            match_len, weight = 0, 0.0
            for n in range(min(self.max_ngram, len(words) - i), 0, -1):
                key = " ".join(words[i : i + n])
                if key in self.weights:
                    match_len, weight = n, self.weights[key]
                    break
            if not match_len:
                i += 1
                continue
            term = " ".join(words[i : i + match_len])
            factor = 1.0
            before = words[max(0, i - cfg.negation_window) : i]
            if any(w in self.negators for w in before):
                factor *= -0.74
            for w in words[max(0, i - cfg.intensifier_window) : i]:
                if w in self.intensifiers:
                    factor *= self.intensifiers[w]
            if all(c for _, c in toks[i : i + match_len]) and not text_is_shouting:
                factor *= cfg.caps_boost
            contrib = weight * factor
            hits.append((term, contrib))
            raw += contrib
            i += match_len

        norm = normalize(text)
        if raw:
            raw += math.copysign(cfg.exclamation_boost * min(norm.count("!"), 4), raw)
        hedge = 1.0
        for w in set(words):
            hedge *= self.hedges.get(w, 1.0)
        if norm.rstrip().endswith("?"):
            hedge *= cfg.question_hedge
        hedge = max(hedge, 0.5)
        compound = raw / math.sqrt(raw * raw + cfg.compound_alpha) if raw else 0.0
        return ScoreResult(sentiment=compound * hedge, raw=raw, hedge=hedge, hits=hits)

    def score_frame(self, df: pd.DataFrame, text_col: str = "text") -> pd.DataFrame:
        results = [self.score(t) for t in df[text_col]]
        return df.assign(
            sentiment=[r.sentiment for r in results],
            raw_score=[r.raw for r in results],
            hedge=[r.hedge for r in results],
            n_hits=[len(r.hits) for r in results],
            matched_terms=[r.matched_terms for r in results],
        )

    def explain(self, text: str) -> pd.DataFrame:
        r = self.score(text)
        rows = [{"term": t, "contribution": c} for t, c in r.hits]
        rows.append({"term": "= sentiment (after normalization & hedges)", "contribution": r.sentiment})
        return pd.DataFrame(rows)
