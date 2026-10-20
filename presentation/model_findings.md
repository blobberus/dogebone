# Model findings (auto-drafted by notebooks/02_direction_model.ipynb)

_Generated 2026-10-20 08:11 UTC from 105 @elonmusk DOGE posts on 69 post days, 2021-01-01 to 2021-12-31. Model: L2 logistic regression (penalty 5, fixed in advance) on post-day text and market features. Focus horizon: 1 day(s), chosen before testing._

## Headline

- Walk-forward (Mar–Dec 2021, refit monthly on earlier months only): the model called the next-1-day direction right **50%** of the time vs. **49%** no-skill (+0.5 pp, p = 0.525, n = 52 post days; AUC 0.52, Brier skill -0.05): **not** distinguishable from chance.
- Held-out Sep–Dec 2021 (trained on Jan–Aug only): the model called the next-1-day direction right **20%** of the time vs. **40%** no-skill (-19.5 pp, p = 0.982, n = 20 post days; AUC 0.36, Brier skill -0.35): **not** distinguishable from chance.
- Against simple rules (walk-forward, 1d): the model beat always calling the training majority (48%) and beat momentum (40%).

## Every horizon (text + market features)

| Test | Horizon | n | Model | No-skill | p | Majority rule | Momentum | AUC | Brier skill |
|---|---|---|---|---|---|---|---|---|---|
| walk-forward | 1d | 52 | 50% | 49% | 0.525 | 48% | 40% | 0.52 | -0.05 |
| walk-forward | 3d | 52 | 62% | 49% | 0.052 | 48% | 56% | 0.59 | +0.07 |
| walk-forward | 7d | 51 | 49% | 50% | 0.620 | 55% | 59% | 0.44 | -0.10 |
| held-out | 1d | 20 | 20% | 40% | 0.982 | 35% | 30% | 0.36 | -0.35 |
| held-out | 3d | 20 | 55% | 52% | 0.483 | 55% | 50% | 0.60 | +0.02 |
| held-out | 7d | 19 | 53% | 57% | 0.735 | 58% | 68% | 0.53 | -0.05 |

_Three horizons were tested, so a single p below 0.05 is weak evidence: the Bonferroni bar is 0.017. A Brier skill above 0 means the probabilities beat the training base rate._

## Is it the words or the market? (walk-forward)

| Features | 1d hit / AUC | 3d hit / AUC | 7d hit / AUC |
|---|---|---|---|
| text + market | 50% / 0.52 | 62% / 0.59 | 49% / 0.44 |
| text only | 52% / 0.50 | 56% / 0.61 | 49% / 0.48 |
| market only | 37% / 0.36 | 40% / 0.31 | 57% / 0.36 |

**Permutation tests** (walk-forward, text + market; p = share of shuffled runs at least as good):

- 1d, outcomes shuffled (are any features informative?): hit-rate p = 0.522, AUC p = 0.355 (300 shuffles).
- 3d, outcomes shuffled (are any features informative?): hit-rate p = 0.030, AUC p = 0.100 (300 shuffles).
- 7d, outcomes shuffled (are any features informative?): hit-rate p = 0.721, AUC p = 0.684 (300 shuffles).
- 1d, Musk's text features shuffled, market kept (do the words add anything?): hit-rate p = 0.415, AUC p = 0.252 (300 shuffles).
- 3d, Musk's text features shuffled, market kept (do the words add anything?): hit-rate p = 0.030, AUC p = 0.033 (300 shuffles).
- 7d, Musk's text features shuffled, market kept (do the words add anything?): hit-rate p = 0.545, AUC p = 0.465 (300 shuffles).

## Does conviction mean anything? (walk-forward, 1d)

| Conviction | n | Mean P(up) | Realized up-rate | Hit rate |
|---|---|---|---|---|
| LOW | 23 | 47% | 57% | 48% |
| MEDIUM | 18 | 50% | 50% | 56% |
| HIGH | 11 | 40% | 45% | 45% |

_HIGH = the model is at least 70% sure either way; LOW = between 40% and 60%._

## What the final 1d model learned (fit on all of 2021)

- DOGE return, last 7 days: +0.32 log-odds per SD (toward UP).
- Number of DOGE posts that day: -0.25 log-odds per SD (toward DOWN).
- Used any sentiment word: -0.24 log-odds per SD (toward DOWN).
- Share of posts saying 'Doge' outright: +0.21 log-odds per SD (toward UP).
- Has an original post (not only replies): +0.12 log-odds per SD (toward UP).

## The held-out test, post day by post day (1d)

| Anchor close | First post that day | P(up) | Call | Conviction | Actual | |
|---|---|---|---|---|---|---|
| 2021-09-02 | @dogecoin_devs Good progress. Applying information theory to currency… | 36% | DOWN | MEDIUM | UP | ❌ |
| 2021-09-12 | @SirWoofOfDoge @WholeMarsBlog 🤣🤣 | 18% | DOWN | HIGH | DOWN | ✅ |
| 2021-09-22 | @BillyM2k Super important for Doge fees to drop to make things like b… | 29% | DOWN | HIGH | UP | ❌ |
| 2021-09-28 | @NewFolderF @dogeofficialceo @BillyM2k 🤣 | 27% | DOWN | HIGH | UP | ❌ |
| 2021-10-22 | @UberFacts *In Dogecoin | 36% | DOWN | MEDIUM | UP | ❌ |
| 2021-10-23 | @mishaboar @DogecoinFdn Neither Jared, nor me, nor anyone I know has … | 48% | DOWN | LOW | UP | ❌ |
| 2021-10-24 | @TeslaGong @mishaboar @DogecoinFdn Not recently. What matters imo is … | 38% | DOWN | MEDIUM | DOWN | ✅ |
| 2021-10-27 | @BillyM2k If I send you 2 Doge, will you promise to send me 1 Doge? | 41% | DOWN | LOW | UP | ❌ |
| 2021-10-31 | Tuition is in Dogecoin & u get a discount if u have a dog | 60% | UP | LOW | DOWN | ❌ |
| 2021-11-01 | @dogeofficialceo @Forbes 🤣 | 50% | DOWN | LOW | UP | ❌ |
| 2021-11-02 | @BillyM2k How about my lil doge Floki? He would make a great CEO! His… | 61% | UP | MEDIUM | DOWN | ❌ |
| 2021-11-05 | @dogeofficialceo @BillyM2k 🤣 | 36% | DOWN | MEDIUM | UP | ❌ |
| 2021-11-15 | @dogeofficialceo @daelmor @SenSanders Regretamine, it's like a 100% t… | 24% | DOWN | HIGH | DOWN | ✅ |
| 2021-11-22 | @CoinDesk @binance @egreechee Hey @cz_binance, what's going on with y… | 39% | DOWN | MEDIUM | UP | ❌ |
| 2021-11-23 | @cz_binance @CoinDesk @binance @egreechee I don't use Binance (tried … | 63% | UP | MEDIUM | DOWN | ❌ |
| 2021-11-24 | @BillyM2k @WSBChairman @joannabanananaa @dogeofficialceo @GailAlfarAT… | 35% | DOWN | MEDIUM | UP | ❌ |
| 2021-11-25 | @GailAlfarATX @SpaceX @RGVaerialphotos @cnunezimages @kanyewest @SciG… | 43% | DOWN | LOW | DOWN | ✅ |
| 2021-12-10 | @GailAlfarATX @SawyerMerritt @dogecoin Imbued gold/bronze color would… | 18% | DOWN | HIGH | UP | ❌ |
| 2021-12-13 | @DOGEHOUNDS @HardcoreHistory Overall kill ratio was 19:1, but kill ra… | 42% | DOWN | LOW | UP | ❌ |
| 2021-12-22 | @BillyM2k @jack @gladstein @rahilla @farokh @samkazemian @TheSmarmyBu… | 42% | DOWN | LOW | UP | ❌ |

## Caveats to say out loud

- One account, one year: about 50 out-of-sample post days per horizon, so a 10-point edge is within noise.
- 2021 changed regime (mania to slow bleed). Relationships learned in Feb–May can flip by the autumn.
- Daily closes blur a minutes-scale reaction; posts are anchored to the nearest close (at most 12h of overlap).
- Features and the penalty were fixed before testing; nothing was tuned on the test months.

## Figures exported for slides

- `presentation/figures/06_model_vs_baselines.png`
- `presentation/figures/07_model_heldout_calls.png`
- `presentation/figures/08_model_coefficients.png`
