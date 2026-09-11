# Cricket Elo

[![Tests](https://github.com/Harvey15th/cricket-data-analysis/actions/workflows/tests.yml/badge.svg)](https://github.com/Harvey15th/cricket-data-analysis/actions/workflows/tests.yml)

A Python command-line project for analysing historical men's Twenty20 International (T20I) cricket matches using Elo ratings.

Cricket Elo prepares raw match data, trains team ratings, evaluates pre-match predictions against a 50/50 baseline, exports individual predictions, and plots cumulative prediction error. It is an educational project focused on practical Python development and reproducible model evaluation.

## What the project does

- Converts Cricsheet JSON files into a consistent match-level CSV.
- Processes matches in deterministic `(date, match_id)` order.
- Trains Elo ratings with a separate K-factor for each team.
- Estimates a matchup using previously generated ratings.
- Evaluates later matches by predicting first and updating ratings afterwards.
- Reports Brier score, a constant-probability baseline, and evaluated/skipped match counts.
- Exports per-match predictions and plots cumulative average Brier score.
- Runs automated unit and integration tests locally and through GitHub Actions.

The package and CLI are implemented. Reproducing the walkthrough from a fresh clone and publishing a tagged release are the final checks for the first versioned release.

## Installation

Requires **Python 3.12 or later** and Git. Matplotlib is installed through the package dependencies; the `dev` extra installs pytest.

The walkthrough below uses **Windows PowerShell**. Run commands from the repository root. It calls the virtual environment's Python directly, so activating the environment is unnecessary.

```powershell
git clone https://github.com/Harvey15th/cricket-data-analysis.git
Set-Location cricket-data-analysis
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m cricket_elo --help
```

If the repository is already cloned, start with `python -m venv .venv` from its root. The `-e` installation lets changes to the source code take effect without reinstalling the package. Reinstall after changing package dependencies.

On macOS or Linux, the equivalent virtual-environment interpreter is `.venv/bin/python`; the application subcommands and arguments are the same. The download, extraction, and here-string examples below use PowerShell syntax.

## Data source

The project uses match data published by [Cricsheet](https://cricsheet.org/downloads/). Download the [men's T20I JSON archive](https://cricsheet.org/downloads/t20s_male_json.zip); the [JSON format documentation](https://cricsheet.org/format/json/) describes its fields.

Archive coverage changes as matches are added or revised. Keep the same archive and cutoff date when reproducing a particular result. Raw JSON, downloaded ZIP archives, and generated CSVs are excluded from Git and must be obtained or generated locally.

## Run the complete workflow

### 1. Download and extract the raw data

```powershell
New-Item -ItemType Directory -Force -Path "data", "data/processed", "outputs" | Out-Null
Invoke-WebRequest -Uri "https://cricsheet.org/downloads/t20s_male_json.zip" -OutFile "data/t20s_male_json.zip"
Expand-Archive -Path "data/t20s_male_json.zip" -DestinationPath "data/t20s_male_json/full_dataset" -Force
```

The match JSON files should sit directly inside `data/t20s_male_json/full_dataset`. If you already have the archive, extract it there and create the `data/processed` and `outputs` folders.

For a repeat run with an updated dataset, use a fresh extraction directory so removed or renamed matches from an older archive are not retained.

### 2. Prepare the match CSV

```powershell
.\.venv\Scripts\python.exe -m cricket_elo prepare --input data/t20s_male_json/full_dataset --output data/processed/matches.csv
```

The output has one row per match and these headers:

```text
match_id,date,team1,team2,result,match_type
```

Dates use `YYYY-MM-DD`. The result contains the winning team's name, `tie`, or `no result`. Prepared matches are ordered by date and then by their string match ID.

### 3. Create separate training and verification periods

This example uses matches **before 1 January 2025** for training and matches **on or after that date** for verification. Keeping whole dates in one period avoids splitting a single day across the training/verification boundary.

Paste the entire block into PowerShell. It uses Python's standard library and preserves the prepared CSV's row order and headers.

```powershell
@'
import csv
from pathlib import Path

folder = Path("data/processed")
cutoff = "2025-01-01"

with (folder / "matches.csv").open(newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    fields = reader.fieldnames
    matches = list(reader)

training = [match for match in matches if match["date"] < cutoff]
verification = [match for match in matches if match["date"] >= cutoff]

if not training or not verification:
    raise ValueError("The cutoff must leave matches in both periods.")

for name, rows in [("training", training), ("verification", verification)]:
    with (folder / f"{name}.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{name}: {len(rows)} matches, {rows[0]['date']} to {rows[-1]['date']}")
'@ | .\.venv\Scripts\python.exe -
```

This produces `data/processed/training.csv` and `data/processed/verification.csv`. Choose and record the cutoff before comparing model variants.

### 4. Evaluate Elo against the baseline

```powershell
.\.venv\Scripts\python.exe -m cricket_elo benchmark --training-data data/processed/training.csv --verification-data data/processed/verification.csv --output outputs/evaluation.csv --predictions-output outputs/predictions.csv
Import-Csv outputs/evaluation.csv | Format-List
```

`benchmark` trains internally on the training CSV, then predicts each verification match before updating the ratings with its result. The `--predictions-output` argument is optional; omit it if you only need the summary.

The evaluation rejects unsorted periods, repeated match IDs, and invalid ordering across the training/verification boundary. A period with no decisive verification matches cannot produce a binary Brier score.

### 5. Plot the evaluation

```powershell
.\.venv\Scripts\python.exe -m cricket_elo plot --eval-log outputs/predictions.csv --output outputs/brier_over_time.png
```

The chart shows the running average Brier score over decisive verification matches. Its final value should match the summary's `brier_score`, allowing for floating-point rounding. Lower is better; the 50/50 baseline is 0.25.

The current command also displays the plot interactively when a graphical backend is available. Close the plot window to return to the terminal. CI uses a non-interactive backend for image generation.

### 6. Train ratings on all available matches

After evaluating the model, train on the full prepared dataset to generate the latest ratings for prediction:

```powershell
.\.venv\Scripts\python.exe -m cricket_elo train --input-data data/processed/matches.csv --output outputs/ratings.csv
```

These ratings include the entire dataset. The earlier benchmark uses only its specified training file to initialise evaluation.

To display the ten highest-rated teams:

```powershell
Import-Csv outputs/ratings.csv | Sort-Object { [double]$_.elo } -Descending | Select-Object -First 10 | Format-Table
```

### 7. Estimate a matchup

```powershell
.\.venv\Scripts\python.exe -m cricket_elo predict --ratings outputs/ratings.csv --team-a "England" --team-b "India"
```

Use team names exactly as they appear in the ratings file. The estimate reflects ratings through the last match in the dataset.

Each subcommand supports `--help`, for example:

```powershell
.\.venv\Scripts\python.exe -m cricket_elo benchmark --help
.\.venv\Scripts\python.exe -m cricket_elo plot --help
```

Successful commands return exit status `0`; failures return a non-zero status. Successful writes replace the files at the requested output paths. Use different output paths to retain earlier runs.

## Model and evaluation

Teams start at **1500 Elo**. For ratings $R_A$ and $R_B$, the model calculates:

$$
p_A = \frac{1}{1 + 10^{(R_B - R_A)/400}}
$$

This expected score is used as the model's probability estimate when scoring decisive matches. A result that was less expected produces a larger rating adjustment.

Each team uses **K = 100** while it has played fewer than seven completed matches, then **K = 64**. K is selected using the count before the current match. Separate K-factors allow newer teams to adjust more quickly; when the factors differ, the combined rating total need not be conserved.

| Outcome | Update Elo and match counts? | Include in binary Brier score? |
|---|---|---|
| Decisive win/loss | Yes; score 1 for the winner and 0 for the loser | Yes |
| Tie | Yes; score 0.5 for each team | No |
| No result | No | No |

The reported Brier score is the mean of `(actual_score - p_team1) ** 2` over decisive verification matches. A constant prediction of 0.5 has Brier score **0.25** on each of those matches.

`brier_improvement` is `baseline_brier_score - brier_score`: positive values mean Elo performed better than the baseline on that period; negative values mean it performed worse.

See [MODEL-SPEC.md](docs/MODEL-SPEC.md) for the model rules.

## Generated outputs

| File used in the walkthrough | Contents |
|---|---|
| `data/processed/matches.csv` | Prepared match records |
| `data/processed/training.csv` | Matches before the cutoff |
| `data/processed/verification.csv` | Matches on or after the cutoff |
| `outputs/ratings.csv` | Team `name`, `elo`, and `matches_played` |
| `outputs/evaluation.csv` | Aggregate scores, improvement, counts, and period boundary dates |
| `outputs/predictions.csv` | One record for every verification match |
| `outputs/brier_over_time.png` | Cumulative mean Brier score chart |

The summary contains `brier_score`, `baseline_brier_score`, `brier_improvement`, `matches_evaluated`, `matches_skipped`, `training_end`, and `verification_start`.

Prediction records contain match details, both pre-match ratings, `p_team1`, `actual_score`, `status`, `elo_brier`, and `baseline_brier`. Status is `evaluated`, `tie`, or `no_result`. Ties and no-results have blank Brier fields; no-results also have a blank `actual_score`.

## Results and limitations

The example chart discussed in [RESULTS.md](docs/RESULTS.md) finishes near **0.196 Brier score**, compared with the **0.250** baseline: approximately **22% lower Brier error**. These figures are estimates from that chart. Use `outputs/evaluation.csv` for the exact numbers from your own run; a different archive or cutoff may produce different results.

The model currently uses team ratings and match outcomes. It does not explicitly model venues, lineups, player availability, conditions, or margin of victory. It also has no explicit rating decay for long periods of inactivity.

Evaluation uses deterministic date-and-match-ID ordering. Within a date, match IDs are a tie-breaker rather than a verified ordering by match start time. The score therefore depends on that ordering convention as well as the dataset and model rules.

A lower score than the 50/50 baseline provides evidence of useful predictions in the evaluated period. Broader conclusions require additional periods, stronger baselines, and checks of probability calibration. The flattening of a cumulative-average chart also reflects averaging over more observations.

Input handling targets the documented Cricsheet and processed-CSV formats; it is not a general validator for arbitrary cricket datasets. Team names must be consistent across the data and command arguments.

## Tests and continuous integration

Run the full suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Run an individual file while developing:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_predictions_export.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_plot.py -v
```

The suite covers Elo calculations, data preparation, training and prediction, chronological evaluation, baseline comparison, prediction exports, and plot generation. Integration tests create temporary fixtures, so running the tests does not require the full cricket dataset.

The [GitHub Actions workflow](.github/workflows/tests.yml) installs the package with its development dependencies and runs the suite on Ubuntu with Python 3.12. It runs for pull requests targeting `main` and pushes to `main`. Matplotlib uses the `Agg` backend to save plots without a desktop window.

## Repository guide

| Path | Purpose |
|---|---|
| `pyproject.toml` | Package metadata, dependencies, and installation configuration |
| `src/cricket_elo/__main__.py` and `cli.py` | Module entry point and CLI argument handling |
| `src/cricket_elo/csv_prepare.py` | JSON preparation and CSV input/output |
| `src/cricket_elo/model.py` and `team.py` | Elo calculations and team rating state |
| `src/cricket_elo/train.py`, `predict.py`, and `benchmark.py` | Training, matchup estimates, and evaluation |
| `src/cricket_elo/plot_evaluation.py` | Plotting evaluation results |
| `tests/` | Unit and integration tests |
| `.github/workflows/tests.yml` | Automated CI test run |
| `docs/` | [Model specification](docs/MODEL-SPEC.md), [results discussion](docs/RESULTS.md), and [Git recovery guide](docs/git-recovery.md) |
| `data/` | Locally downloaded and processed datasets |
| `outputs/` | Generated ratings, evaluation summaries, predictions, and charts |

## Licence

The software is distributed under the [MIT licence](LICENSE). Match data is provided by Cricsheet; refer to the documentation supplied with the downloaded archive for its attribution and usage terms.
