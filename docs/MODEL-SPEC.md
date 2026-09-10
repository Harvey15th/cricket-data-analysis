# Cricket Elo — Model Specification

**Specification version:** 1.0  
**Project stage:** Prototype  
**Model scope:** Men's T20 international cricket  
**Purpose:** Define the behaviour of the Elo model independently of its Python implementation

## 1. Purpose

The Cricket Elo model converts a chronological sequence of match results into:

- a continuously updated rating for each team;
- a pre-match expected score for each team; and
- an evaluation of how informative those expected scores are on later matches.

This document is the source of truth for the model's intended behaviour. Implementation details such as classes, dictionaries, filenames and command-line parsing belong elsewhere. If the code and this specification disagree, either the code must be corrected or this document must be deliberately revised.

The project is an educational statistical model. Its outputs are not intended for wagering or financial decisions.

## 2. Scope

The current rating pool contains men's T20 international teams. Matches from other formats or competitions must not be mixed into the same pool unless separate pools are introduced explicitly.

The first version uses match outcomes only. It does not account for:

- venue or home advantage;
- margin of victory;
- player selection or availability;
- toss outcome;
- innings-level or ball-by-ball information;
- rating decay; or
- changes in team identity or naming.

These may be investigated later, after the base model has been tested and evaluated.

## 3. Inputs

Each processed match must provide at least:

| Field | Meaning |
| --- | --- |
| Match identifier | A unique, stable identifier |
| Date | The date used to order matches |
| Team A | The first team in the record |
| Team B | The second team in the record |
| Result | Team A, Team B, `tie`, or `no result` |
| Match type | Used to ensure only eligible matches enter this rating pool |

The following input rules apply:

1. Team A and Team B must be different.
2. A named winner must be either Team A or Team B.
3. Match identifiers must be unique.
4. Matches must be processed by date, with match identifier used as a deterministic tie-breaker.
5. Unsupported or malformed records must produce a clear error rather than being silently reinterpreted.

## 4. Rating state

For each team, the model stores:

- its current Elo rating; and
- its number of completed rated matches.

An unseen team begins with:

| Parameter | Value |
| --- | ---: |
| Initial rating | 1500 |
| Completed rated matches | 0 |

A no-result match does not count as a completed rated match.

## 5. Expected score

Let \(R_A\) and \(R_B\) be the ratings of Teams A and B immediately before a match. Team A's expected score is

$$
E_A = \frac{1}{1 + 10^{(R_B-R_A)/400}}.
$$

Team B's expected score is

$$
E_B = 1-E_A.
$$

Required properties:

- Equal ratings produce an expected score of \(0.5\) for each team.
- Increasing \(R_A\) while holding \(R_B\) fixed increases \(E_A\).
- Swapping the teams gives complementary expected scores.
- Expected scores are strictly between 0 and 1 for finite ratings.

The expected score must be calculated and recorded before the result of that match is used to update either rating.

## 6. Match score

The actual score for Team A, written \(S_A\), is:

| Result | \(S_A\) |
| --- | ---: |
| Team A wins | 1.0 |
| Team B wins | 0.0 |
| Tie | 0.5 |
| No result | No score; skip the rating update |

For a completed match, Team B's actual score is \(S_B=1-S_A\).

The model must represent a no-result separately from a numeric score. It must not pass a text value into rating arithmetic.

## 7. Adaptive K-factor

The K-factor controls how quickly a team's rating responds to new information. This model intentionally gives provisional teams a larger K-factor so that their ratings can reach a plausible level more quickly.

| Completed rated matches before the match | K-factor |
| ---: | ---: |
| 0–6 | 100 |
| 7 or more | 64 |

Therefore, each team's K-factor is selected independently from its own match count:

$$
K_A = K(n_A), \qquad K_B = K(n_B).
$$

A team's eighth completed rated match is its first match played using the established-team K-factor of 64.

Ties count as completed rated matches. No-results do not.

## 8. Rating update

For a completed match, calculate the rating error from Team A's perspective:

$$
d = S_A-E_A.
$$

Update the ratings using the teams' independently selected K-factors:

$$
R'_A = R_A + K_A d,
$$

$$
R'_B = R_B - K_B d.
$$

The ratings may be stored internally as floating-point values. Rounding is for display or exported reports only and must not affect later updates.

### 8.1 Unequal K-factors and rating-pool drift

When \(K_A=K_B\), the gain by one team exactly equals the loss by the other, so the pair's total rating is conserved.

When \(K_A\ne K_B\), the total change is

$$
(R'_A+R'_B)-(R_A+R_B)=(K_A-K_B)d.
$$

The rating pool can therefore gain or lose points when a provisional team plays an established team. This is an accepted consequence of faster adaptation for new teams, not an implementation error. Evaluation should monitor the average rating through time so that excessive drift is visible.

## 9. Chronological processing

Matches must be processed in true chronological order. For every eligible match:

1. Read both teams' current pre-match state.
2. Calculate both K-factors from pre-match completed-match counts.
3. Calculate and, where required, record the pre-match expected score.
4. Interpret the result.
5. If the match is a no-result, leave ratings and match counts unchanged.
6. Otherwise, update both ratings and increment both match counts once.

Sorting by a match identifier alone is not sufficient unless that identifier is proven to be chronological.

## 10. Training behaviour

Training consumes an earlier chronological collection of matches and produces one final state per team.

The training output must contain at least:

| Field | Meaning |
| --- | --- |
| Team name | Unique team identifier |
| Final rating | Full-precision internally; may be rounded for display |
| Completed rated matches | Excludes no-results |

Repeated runs with the same input and configuration must produce the same output. A run must replace its own generated output rather than append duplicate results from an earlier run.

## 11. Benchmark behaviour

The benchmark uses earlier matches to establish ratings and later, unseen matches to assess the model.

For each verification match, it must:

1. calculate the expected score before updating the teams;
2. save or accumulate the prediction and observed outcome;
3. update the ratings only after scoring the prediction; and
4. continue chronologically to the next match.

This order prevents future-information leakage.

### 11.1 Headline metric

For decisive verification matches, the Brier score is

$$
\text{Brier} = \frac{1}{N}\sum_{i=1}^{N}(S_{A,i}-E_{A,i})^2,
$$

where \(N\) is the number of decisive matches actually evaluated.

- Lower is better.
- No-results are excluded from both the numerator and denominator.
- Ties may update ratings but are excluded from this binary headline metric.
- The benchmark must report \(N\) alongside the score.
- The same matches must also be evaluated using a constant \(0.5\) baseline.

If ties are instead included with a target of 0.5, that result must be labelled mean squared error rather than a binary Brier score and reported separately.

### 11.2 Secondary diagnostics

Useful secondary results include:

- prediction accuracy on decisive matches;
- calibration by probability band;
- performance by year;
- the number of skipped ties and no-results; and
- the mean rating of the pool through time.

## 12. Model invariants

The implementation and tests should enforce these invariants:

1. Pre-match probabilities are computed before updating ratings.
2. Team A and Team B expected scores sum to 1, subject to floating-point tolerance.
3. A winner gains rating and a loser loses rating.
4. An upset causes a larger absolute update than an expected win under the same K-factors.
5. A provisional team moves more than an established team for the same prediction error.
6. Equal K-factors conserve the two teams' total rating.
7. No-results change neither ratings nor completed-match counts.
8. Every completed match increments each participating team's count exactly once.
9. Re-running an identical experiment gives identical results.
10. Verification results never influence their own pre-match predictions.

## 13. Minimum automated test coverage

The model is not considered verified until automated tests cover:

- equal-rating and unequal-rating expected scores;
- probability symmetry;
- win, loss, tie and no-result score interpretation;
- both sides of the K-factor threshold;
- equal-K and unequal-K rating updates;
- rating conservation when K-factors match;
- faster movement for provisional teams;
- a small end-to-end training example;
- no-result handling through the training pipeline; and
- a small chronological benchmark example with no future leakage.

Tests should use tiny synthetic teams and match files. The full Cricsheet archive is too large and changeable to serve as a unit or integration-test fixture.

## 14. Assumptions and limitations

- Elo ratings measure strength relative to this dataset and configuration; they are not absolute measures of team quality.
- A starting rating of 1500 is a convention, not an empirical estimate.
- The K-factor values and seven-match threshold are modelling choices that require evaluation against alternatives.
- Unequal K-factors permit rating-pool drift.
- Expected scores are not guaranteed to be well calibrated probabilities.
- Team-name changes and aliases can accidentally create separate teams.
- The model ignores contextual information that may affect match outcomes.
- Historical coverage and corrections in the source data can alter results.
- Performance on past matches does not guarantee performance on future matches.

## 15. Change control

Any change to the following constitutes a model change and must update this document, its version, and the relevant tests:

- starting rating;
- Elo scale;
- K-factor values or threshold;
- treatment of ties or no-results;
- match ordering;
- rating-update formula;
- rating-pool membership; or
- benchmark population or metric.

Refactoring code without changing these behaviours is an implementation change and does not require a new model version.
