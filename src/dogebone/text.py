"""Text normalization, emoji-aware tokenization, and DOGE context tagging (coin vs. government dept)."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

URL_RE = re.compile(r"https?://\S+|www\.\S+")
# Skin tones, variation selectors, and zero-width joiners carry no sentiment; drop them so emoji match.
EMOJI_NOISE_RE = re.compile("[\U0001F3FB-\U0001F3FF︎️‍]")
EMOJI_CLASS = "[\U0001F000-\U0001FAFF☀-➿⬀-⯿]"
TOKEN_RE = re.compile(r"[$#@]?[a-z0-9]+(?:'[a-z]+)?|" + EMOJI_CLASS, re.IGNORECASE)
ELONGATION_RE = re.compile(r"([a-z])\1{2,}", re.IGNORECASE)  # "moooon" -> "moon"

STOPWORDS = frozenset(
    """a an the and or but if then so of to in on at by for with from as is are was were be been being am
    it its it's this that these those i me my we our you your he him his she her they them their what which
    who whom whose when where why how all any both each few more most other some such only own same than too
    s t can will just do does did doing have has had having would should could there here up down out over
    under again further once about into through during before after above below off rt amp via u im
    """.split()
)


def normalize(text: str) -> str:
    """NFKC folds 'fancy font' unicode (𝐃𝐎𝐆𝐄 -> DOGE); URLs carry no sentiment."""
    text = unicodedata.normalize("NFKC", str(text))
    text = text.replace("’", "'").replace("‘", "'")
    text = URL_RE.sub(" ", text)
    text = EMOJI_NOISE_RE.sub("", text)
    return ELONGATION_RE.sub(r"\1\1", text)


def tokenize(text: str) -> list[tuple[str, bool]]:
    """Return (lowercase_token, was_all_caps) pairs. Hashtag '#' is stripped; '$' and '@' kept."""
    out = []
    for m in TOKEN_RE.finditer(normalize(text)):
        tok = m.group(0)
        is_caps = tok.isupper() and sum(ch.isalpha() for ch in tok) >= 2
        low = tok.lower()
        if low.startswith("#"):
            low = low[1:]
        out.append((low, is_caps))
    return out


def _is_content(tok: str) -> bool:
    if tok in STOPWORDS or tok.startswith("@") or tok.isdigit():
        return False
    return len(tok) > 1 or not tok.isascii()  # single characters survive only if they're emoji


def content_tokens(text: str) -> list[str]:
    """Tokens for keyword discovery: lowercase, no stopwords, no @mentions, no bare numbers."""
    return [t for t, _ in tokenize(text) if _is_content(t)]


def ngrams(tokens: list[str], n_max: int = 2) -> set[str]:
    grams = set(tokens)
    for n in range(2, n_max + 1):
        grams.update(" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1))
    return grams


class ContextTagger:
    """Tag a post 'coin' when it clearly refers to Dogecoin the asset; otherwise fall back to the account's
    default context, else 'ambiguous' (bare 'doge' memes, dog photos, Floki jokes). Ambiguous posts still
    count, at a lower conviction weight.
    """

    def __init__(self, lexicon_path: Path, account_default_context: dict | None = None):
        lex = pd.read_csv(lexicon_path)
        self.pattern = re.compile("|".join(self._pattern(t) for t in lex["term"]), re.IGNORECASE)
        self.account_default_context = account_default_context or {}

    @staticmethod
    def _pattern(term: str) -> str:
        esc = re.escape(term.lower())
        if term[0].isalnum() or term[0] in "$@":
            esc = r"(?<![\w$@])" + esc
        if term[-1].isalnum():
            esc = esc + r"(?!\w)"
        return esc

    def tag(self, text: str, username: str | None = None) -> str:
        if self.pattern.search(normalize(text).lower()):
            return "coin"
        return self.account_default_context.get(username, "ambiguous")
