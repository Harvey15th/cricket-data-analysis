# Cricket Elo — Design Specification

**Status:** Editable baseline (version 0.1)  
**Project name:** `cricket-elo`  
**Primary language:** Python 3.12+  
**Initial scope:** Men's T20 internationals  
**Purpose:** A small, correct and reproducible quantitative software project

## 1. Product summary

`cricket-elo` reads historical cricket match results in chronological order, maintains an Elo rating for each team, produces a win probability before every match, and measures how well those probabilities predict later results.

The project is intended to demonstrate more than a formula. It should show a complete software workflow: acquiring data, validating and transforming it, implementing a model, preventing data leakage, evaluating probabilistic predictions, testing important behaviour, producing useful outputs, and documenting how another person can reproduce the results.

## 2. Intended user and use cases

The first user is the developer of the project. A second user is a reviewer who clones the repository and wants to understand and reproduce the analysis without editing source code.

The program should let a user:

1. Convert a supported Cricsheet archive into a clean match-level dataset.
2. Run the Elo model over matches in chronological order.
3. View the latest team rankings.
4. Inspect the probability predicted before each historical match.
5. Evaluate the Elo model against a simple baseline.
6. Generate a small set of charts and machine-readable result files.
7. Request a probability for a hypothetical match between two currently rated teams.

## 3. Recommended dataset

### 3.1 Primary source

Use **Cricsheet**, which publishes structured cricket match data and provides archives split by match type, competition, team, year and gender.

Recommended starting archive:

- Men's T20 internationals, JSON: <https://cricsheet.org/downloads/t20s_male_json.zip>
- Downloads catalogue: <https://cricsheet.org/downloads/>
- JSON format documentation: <https://cricsheet.org/format/json/>
- Coverage notes: <https://cricsheet.org/coverage/>

As checked on 5 September 2026, the archive contains 3,532 men's T20 internationals. Cricsheet's men's T20I coverage begins in February 2005. The published archive changes as matches are added or revised, so each experiment must record the download date and a file checksum.

### 3.2 Why this dataset

Cricsheet JSON contains every match-level field required by the MVP:

- match date;
- two team names;
- match type and gender;
- winner, tie or no-result status;
- competition/event;
- venue and city where available;
- result method and winning margin where available.

The source is actually richer than the MVP needs because it also includes ball-by-ball data. The ingestion step should deliberately extract only match-level information. This keeps the model simple while leaving a credible route to later feature engineering.

JSON should be preferred over Cricsheet's CSV variants because Cricsheet identifies JSON as its official, most complete and most likely-to-be-updated format. The program's own processed output will still be a straightforward CSV.

### 3.3 Scope decision

The MVP uses one homogeneous rating pool: men's T20 internationals only. It must not mix Test, ODI and T20 results, because a team's strength can differ by format. It must not combine men's and women's teams solely by display name.

Later, the same code may support separate rating pools keyed by `(gender, match_type)`. This is an extension, not an MVP requirement.

### 3.4 Data limitations

- Cricsheet coverage is broad but not guaranteed to be complete.
- Some matches are withheld from the published archives; this must be stated in the final analysis.
- Team names may change or require aliases over time.
- Venue and city are optional fields and are not reliable enough to be core MVP inputs.
- The archive may be revised, so results are reproducible only when the source snapshot is identified.
- Raw Cricsheet data should be attributed in the repository README, and notices or terms supplied with the archive should be retained.

## 4. Processed data contract

The ingestion step will create `data/processed/matches.csv`, with one row per match.

| Column | Type | Required | Meaning |
| --- | --- | --- | --- |
| `match_id` | string | yes | Stable identifier, normally derived from the source filename |
| `date` | ISO date | yes | First match date, used for chronological ordering |
| `team_1` | string | yes | First team in the source record |
| `team_2` | string | yes | Second team in the source record |
| `winner` | string/null | yes | Winning team; null for tie, draw or no result |
| `result` | enum | yes | `team_1_win`, `team_2_win`, `tie`, or `no_result` |
| `match_type` | string | yes | Expected to be `T20` for the MVP input |
| `gender` | string | yes | Expected to be `male` for the MVP input |
| `competition` | string/null | no | Event or series name where supplied |
| `venue` | string/null | no | Venue where supplied |
| `city` | string/null | no | City where supplied |
| `outcome_method` | string/null | no | D/L, DLS, awarded result or another special method |
| `margin_runs` | integer/null | no | Winning margin in runs |
| `margin_wickets` | integer/null | no | Winning margin in wickets |

Invariants:

- `team_1` and `team_2` must differ.
- A named `winner` must equal either `team_1` or `team_2`.
- Match IDs must be unique.
- Rows must be sorted by `date`, then `match_id` for deterministic handling of same-day matches.
- Invalid records must produce a clear validation error rather than being silently changed.
- `no_result` matches do not update ratings and are not evaluated.
- Tied matches update Elo using an actual score of `0.5` for each team but are excluded from the MVP's binary accuracy and Brier score.

## 5. Elo model

### 5.1 Default parameters

| Parameter | Default | Purpose |
| --- | ---: | --- |
| Initial rating | 1500 | Starting value for a team before its first observed match |
| K-factor | 20 | Controls how strongly one result changes a rating |
| Elo scale | 400 | Controls how rating differences map to probabilities |

The expected score for team A is:

```text
P(A) = 1 / (1 + 10 ** ((rating_B - rating_A) / 400))
```

After a completed match:

```text
new_rating_A = rating_A + K * (actual_A - P(A))
new_rating_B = rating_B + K * (actual_B - P(B))
```

For a team-A win, `actual_A = 1` and `actual_B = 0`; for a team-B win, these values are reversed; for a tie, both values are `0.5`.

### 5.2 Required model behaviour

- Calculate and store a prediction before using the result of that match.
- Update both ratings after the result, preserving the total number of rating points in the two-team update.
- Never read future results when constructing a historical prediction.
- Give an unseen team the configured initial rating.
- Make all parameters explicit in a configuration file or command-line options.
- Produce deterministic results for the same input and configuration.

Home advantage, margin-of-victory multipliers, rating decay and team-strength features are deliberately excluded from the MVP. They may be added only after the basic model has been evaluated.

## 6. Evaluation design

### 6.1 Chronological procedure

1. Sort all valid matches by date and match ID.
2. Use the oldest 70% of completed matches as a warm-up period.
3. During warm-up, predict each match and then update ratings, but do not include those predictions in the headline test metrics.
4. Use the newest 30% as the test period.
5. For every test match, save the pre-match probability, observe the result, then update the ratings.
6. Freeze evaluation rules and default parameters before inspecting test performance.

The split date and exact counts must be written to the result summary. A future tuning feature may select K using only the warm-up data; the held-out test period must never be used for parameter selection.

### 6.2 Metrics

Required metrics:

- **Brier score:** mean squared error between the predicted probability for `team_1` and the binary outcome. Lower is better.
- **Accuracy:** whether the team assigned probability greater than `0.5` won. This is secondary because it ignores confidence.
- **Number of evaluated matches:** needed to interpret every metric.

Required baseline:

- Predict `0.5` for each team in every match.

The report must compare Elo with the 0.5 baseline. Beating it is a result to measure, not a condition that should be assumed.

Useful later metrics and diagnostics:

- log loss;
- calibration plot;
- metric breakdown by year or team;
- bootstrap confidence intervals.

### 6.3 Prediction output

Create `outputs/predictions.csv` containing:

- match ID and date;
- both teams;
- both pre-match ratings;
- predicted probability for each team;
- observed winner/result;
- whether the row belongs to warm-up or test;
- both post-match ratings.

Create `outputs/metrics.json` containing the configuration, data snapshot metadata, split details, baseline metrics and Elo metrics.

## 7. Command-line interface

The exact command names may change, but the MVP should support this workflow:

```bash
python -m src/cricket_elo prepare `
  --input data/t20s_male_json `
  --output data/processed/matches.csv

python -m cricket_elo evaluate `
  --matches data/processed/matches.csv `
  --output-dir outputs

python -m cricket_elo rankings --top 20

python -m cricket_elo predict --team-a England --team-b India
```

Every command must provide `--help`, use a non-zero exit status on failure, and print a concise summary of what it created.

## 8. Outputs and charts

Required outputs:

- processed match-level CSV;
- per-match predictions CSV;
- final rankings CSV;
- metrics JSON;
- rating-history line chart for a small, configurable set of teams;
- README instructions and a short results discussion.

Optional after the MVP:

- calibration chart;
- interactive dashboard;
- separate comparisons across match formats;
- automated refresh of the source archive.

Charts must have titles, labelled axes, readable legends and the data snapshot date. They should support the analysis rather than merely decorate the repository.

## 9. Proposed repository structure

```text
cricket-elo/
├── README.md
├── DESIGN_SPEC.md
├── pyproject.toml
├── .gitignore
├── data/
│   ├── raw/                 # downloaded archive; normally git-ignored
│   ├── processed/           # generated match-level data; normally git-ignored
│   └── sample/              # tiny committed fixture for examples/tests
├── outputs/                 # generated results; policy explained in README
├── src/
│   └── cricket_elo/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── data.py
│       ├── model.py
│       ├── evaluate.py
│       └── plots.py
└── tests/
    ├── fixtures/
    ├── test_data.py
    ├── test_model.py
    ├── test_evaluate.py
    └── test_cli.py
```

Suggested direct dependencies are `pandas` and `matplotlib`; use `pytest` for tests. Prefer the standard library's `argparse` for the first CLI unless there is a clear reason to add a CLI framework. Pin or lock dependency versions so a clean clone remains reproducible.

## 10. Functional requirements

| ID | Requirement | MVP priority |
| --- | --- | --- |
| FR-01 | Read a Cricsheet JSON ZIP archive without manually extracting every file | Must |
| FR-02 | Validate match type, gender, team names, dates and outcome | Must |
| FR-03 | Produce the documented match-level CSV | Must |
| FR-04 | Calculate pre-match Elo probabilities | Must |
| FR-05 | Update ratings chronologically after each completed result | Must |
| FR-06 | Handle wins, ties and no-results according to the documented policy | Must |
| FR-07 | Evaluate on a chronological held-out period | Must |
| FR-08 | Report Brier score, accuracy and evaluated-match count | Must |
| FR-09 | Compare results against a 0.5 probability baseline | Must |
| FR-10 | Export predictions, metrics, rankings and rating history | Must |
| FR-11 | Expose prepare, evaluate, rankings and predict CLI commands | Should |
| FR-12 | Generate at least one rating-history chart | Should |

## 11. Non-functional requirements

- **Correctness:** Prediction must occur before rating update, and tests must protect this ordering.
- **Reproducibility:** Record source URL, download date, SHA-256 checksum, configuration and package versions.
- **Clarity:** Use small functions, type hints, docstrings where behaviour is not obvious, and informative error messages.
- **Testability:** Core Elo calculations must be pure functions without file-system or plotting side effects.
- **Portability:** A clean clone should work on Windows, macOS and Linux using documented commands.
- **Performance:** The full initial archive should run comfortably on an ordinary laptop; optimisation is secondary to correctness.
- **Maintainability:** Data parsing, model logic, evaluation and presentation should remain separate modules.

## 12. Minimum test plan

At least these tests should pass:

1. Equal ratings produce probabilities of `0.5` and `0.5`.
2. The two predicted probabilities sum to one.
3. A winner gains rating points and the loser loses the same number.
4. An upset causes a larger rating change than an expected win.
5. An unseen team receives the initial rating.
6. A tie between equally rated teams leaves both ratings unchanged.
7. A no-result match is neither evaluated nor used to update ratings.
8. The loader maps a normal Cricsheet outcome correctly.
9. The loader rejects a winner that is not one of the two teams.
10. An end-to-end fixture proves that each prediction uses only prior matches.

## 13. Definition of done for version 1.0

Version 1.0 is complete when:

- a clean clone can install the project using the README;
- one documented command prepares the data;
- one documented command reproduces the main evaluation and outputs;
- the program reports Elo and baseline metrics on a chronological test period;
- at least five meaningful automated tests pass, with the target test plan above substantially covered;
- generated charts and tables are readable and traceable to a source snapshot;
- limitations, outcome-handling rules and data attribution are documented;
- the repository has a clear commit history with at least five meaningful commits.

## 14. Staged implementation plan

### Milestone 1 — Vertical slice

- Create the package and test structure.
- Manually create or commit a tiny legal sample CSV with a few matches.
- Implement expected-score and rating-update functions.
- Run one match through the model and add core unit tests.

### Milestone 2 — Real data pipeline

- Download the Cricsheet archive outside Git.
- Parse its JSON files directly from the ZIP.
- Validate and write `matches.csv`.
- Add loader and outcome-policy tests.

### Milestone 3 — Chronological evaluation

- Implement predict-then-update processing.
- Add the warm-up/test split.
- Calculate Elo and baseline metrics.
- Export predictions, rankings and metrics.

### Milestone 4 — Communication and polish

- Add charts.
- Write the README and results discussion.
- Test the documented workflow from a clean environment.
- Record limitations and possible extensions.

## 15. Explicit non-goals for the MVP

- Live match ingestion or live predictions.
- Ball-by-ball or player-level modelling.
- A database or hosted web service.
- Machine-learning models beyond the Elo baseline.
- Mixing match formats in one rating pool.
- Optimising parameters on the held-out test period.
- A dashboard before the CLI and evaluation pipeline are reliable.

## 16. Decisions to revisit after the MVP

1. Should men's and women's competitions be supported as separately keyed rating pools?
2. Should each format use a different K-factor?
3. Should ratings regress toward the mean after long inactivity?
4. Should venue or home advantage be modelled?
5. Should margin of victory affect the update size?
6. Should a calibration model be fitted on a validation period?
7. Should raw data acquisition become an automated command?

These questions are deliberately postponed so that version 1 remains small enough to finish, test and explain.
