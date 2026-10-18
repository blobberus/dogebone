"""Single source of truth for every tunable knob. Override fields in the notebook's config cell."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Config:
    # --- Data -------------------------------------------------------------------------------
    data_mode: str = "auto"  # "auto" (raw if present, else sample) | "raw" | "sample"
    analysis_start: str = "2021-01-01"
    analysis_end: str = "2022-12-31"
    # Calibrate on 2021 (bubble), test out-of-sample on 2022 (bear market): a deliberate regime-shift test.
    train_end: str = "2021-12-31"
    include_retweets: bool = False
    # CoinGecko-style files stamp the 00:00 UTC snapshot, which is the *previous* day's close.
    price_is_start_of_day_snapshot: bool = False

    # --- Post -> price alignment --------------------------------------------------------------
    horizons: tuple[int, ...] = (1, 3, 7)  # trading days (crypto trades 7 days/week)
    # nearest_close: anchor on whichever daily close is closer in time to the post (<=12h contamination)
    # prev_close:    anchor on the close before the post's UTC day (captures same-day reaction)
    # same_close:    anchor on the close of the post's UTC day (strictly after; misses intraday reaction)
    anchor_mode: str = "nearest_close"
    date_only_anchor_mode: str = "same_close"  # used when timestamps have no time of day
    flat_band: float = 0.0  # |return| <= band counts as FLAT and is excluded from hit rate
    beta_window: int = 90  # rolling window (days) for DOGE-vs-BTC beta, when BTC prices exist

    # --- Lexicon scoring ----------------------------------------------------------------------
    neutral_threshold: float = 0.05  # |sentiment| below this -> NEUTRAL (no call)
    compound_alpha: float = 15.0  # VADER normalization constant
    negation_window: int = 3
    intensifier_window: int = 2
    caps_boost: float = 1.25
    exclamation_boost: float = 0.292  # per '!', max 4 (VADER)
    question_hedge: float = 0.9
    context_weights: dict = field(default_factory=lambda: {"coin": 1.0, "ambiguous": 0.7})
    account_weight_power: float = 0.5  # conviction uses (influence / max_influence) ** power
    default_account_weight: float = 1.0

    # --- Keyword discovery (data-learned lexicon) -----------------------------------------------
    discovery_horizon: int = 1
    min_term_count: int = 5
    learned_z_min: float = 1.0
    smoothing: float = 1.0

    # --- Paths --------------------------------------------------------------------------------
    root: Path = REPO_ROOT

    @property
    def raw_prices_dir(self) -> Path:
        return self.root / "data" / "raw" / "prices"

    @property
    def raw_tweets_dir(self) -> Path:
        return self.root / "data" / "raw" / "tweets"

    @property
    def sample_dir(self) -> Path:
        return self.root / "data" / "sample"

    @property
    def processed_dir(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def events_path(self) -> Path:
        return self.root / "data" / "reference" / "key_events.csv"

    @property
    def accounts_path(self) -> Path:
        return self.root / "config" / "accounts.csv"

    @property
    def lexicon_dir(self) -> Path:
        return self.root / "lexicons"

    @property
    def figures_dir(self) -> Path:
        return self.root / "reports" / "figures"

    @property
    def presentation_dir(self) -> Path:
        return self.root / "presentation"
