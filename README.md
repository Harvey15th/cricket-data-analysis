# Cricket Elo

A Python project for analysing historical men's Twenty20 International (T20I) cricket matches using an Elo rating system.

The project aims to convert raw match data into a consistent format, maintain chronological team ratings, evaluate the quality of those ratings and estimate pre-match win probabilities.

## The Problem

Given a collection of historical T20I matches in JSON format, this project aims to:

1. Convert the raw files into a consistent match-level dataset.
2. Process matches chronologically.
3. Calculate each team's Elo rating after every completed match.
4. Generate pre-match win probabilities.
5. Evaluate those probabilities against historical results and a simple baseline.
6. Provide a consistent command-line interface for preparing data, running evaluations and viewing results.

The main challenge is ensuring that every prediction uses only information that would have been available before the match. This prevents future information from leaking into the evaluation.

## Why Elo?

The Elo rating system accounts for the relative strength of the two teams involved in a match.

Defeating a highly rated opponent should produce a larger rating increase than defeating a much weaker opponent. Similarly, an unexpected loss should have a greater effect than a loss that the model already considered likely.

Elo also provides an interpretable expected score that can be used as a pre-match win probability. This makes it a useful baseline before attempting more complicated statistical or machine-learning models.

## Project Status

This project is currently an early prototype and is still under active development.

The current implementation can:

* Convert a directory of Cricsheet JSON files into a simplified CSV dataset.
* Train basic Elo ratings from processed match data.
* Export final team ratings.
* Estimate the win probability between two known teams.
* Run an experimental benchmark on a later group of matches.

The current benchmark is not yet considered reliable because several correctness and evaluation issues still need to be fixed. Results produced by the current version should therefore not be treated as validated forecasting evidence.

This is an educational data-analysis project and is not intended for real-time or wagering decisions.

## Data Source

The project is designed around match data published by [Cricsheet](https://cricsheet.org/), an open cricket-data project.

Useful resources:

* [Cricsheet downloads](https://cricsheet.org/downloads/)
* [Men's T20I JSON download](https://cricsheet.org/downloads/t20s_male_json.zip)
* [Cricsheet JSON format documentation](https://cricsheet.org/format/json/)
* [Kaggle mirror of the Cricsheet data](https://www.kaggle.com/datasets/suvroo/cricsheet-public-data/data)

The current local dataset contains men's T20I matches beginning in 2005. Coverage depends on the date on which the Cricsheet archive was downloaded.

Raw data and generated CSV files are excluded from Git because of their size. Anyone reproducing the project must download the data separately and follow the relevant Cricsheet attribution and licensing requirements.

## Repository Structure

```text
cricket-data-analysis/
├── README.md
├── LICENSE
├── docs/
│   ├── DESIGN-SPEC.md
│   └── git-recovery.md
├── data/
│   ├── processed/
│   │   ├── matches.csv
│   │   └── benchmarkData.csv
│   └── t20s_male_json/
│       └── full_dataset/
├── outputs/
│   ├── resulting_elo.csv
│   └── validation_elos.csv
├── src/
│   └── cricket_elo/
│       ├── __main__.py
│       ├── prepare.py
│       ├── team.py
│       ├── train.py
│       ├── predict.py
│       └── benchmark.py
└── tests/
```

The `data` and `outputs` directories shown above are generated locally and may not be present in a fresh clone.

## Requirements

The current prototype uses the Python standard library and requires Python 3.12 or later.

The project does not yet have a complete installation configuration. Commands must currently be executed from the repository root.

## Current Working Commands

These commands describe the current prototype interface. They will be replaced by package subcommands later in development.

### Prepare match data

```bash
python src/cricket_elo/prepare.py --input data/t20s_male_json/full_dataset --output data/processed/matches_new.csv
```

This reads the JSON files from the input directory and writes a simplified match-level CSV.

The preparation script currently appends to an existing output file. Use a new output filename to avoid accidentally duplicating records.

### Train Elo ratings

```bash
python src/cricket_elo/__main__.py --mode train -input_data data/processed/matches.csv -output_path outputs/resulting_elo_new.csv
```

This processes the supplied matches and writes one final rating for each team.

The training command also currently appends to an existing output file, so a new output filename should be used for each run.

### Predict a match

```bash
python src/cricket_elo/__main__.py --mode predict -input_data outputs/resulting_elo.csv -team_1 England -team_2 India
```

This reads previously generated ratings and prints the estimated win probability for the first team.

Both team names must appear exactly as they are written in the ratings file.

### Run the experimental benchmark

```bash
python src/cricket_elo/__main__.py --mode benchmark -input_data data/processed/matches.csv -input_data_verification data/processed/benchmarkData.csv
```

This command executes, but its metric is currently affected by known implementation errors and should not yet be interpreted.

## Planned Final Commands

The intended final interface is:

```bash
python -m cricket_elo prepare --input data/t20s_male_json --output data/processed/matches.csv
```

```bash
python -m cricket_elo evaluate --matches data/processed/matches.csv --output-dir outputs
```

```bash
python -m cricket_elo rankings --ratings outputs/rankings.csv --top 20
```

```bash
python -m cricket_elo predict --ratings outputs/rankings.csv --team-a England --team-b India
```

Every command should eventually provide useful `--help` output, validate its inputs and return a non-zero exit status when it cannot complete successfully.

## Known Limitations and Bugs

The current prototype has the following known issues:

* The package cannot yet be run successfully using `python -m cricket_elo`.
* There is no `pyproject.toml` or documented installation procedure.
* The current data-preparation output contains only six columns rather than the complete schema described in `DESIGN-SPEC.md`.
* Data-preparation and training outputs are opened in append mode, which can duplicate data across repeated runs.
* The parser does not sufficiently validate malformed or unsupported input files.
* Matches are reordered by their string match IDs during training, which can destroy chronological ordering.
* Elo updates can use different K-factors for the two teams, meaning rating points are not always conserved.
* Several modules store state in global mutable dictionaries and lists.
* The benchmark contains an incorrect winner comparison.
* Ties and no-results are not yet handled consistently in the evaluation metric.
* The benchmark does not yet report accuracy, sample size or a constant-probability baseline.
* No automated tests have been implemented.
* No automated GitHub Actions workflow exists.
* Rating-history charts and other model diagnostics have not been implemented.
* The current `.gitignore` rules are too broad to support committed JSON and CSV test fixtures.

## Planned Milestones

| Milestone                                                         | Status      |
| ----------------------------------------------------------------- | ----------- |
| Choose the data source and write the initial design specification | Complete    |
| Create the initial JSON-to-CSV converter                          | Complete    |
| Implement prototype Elo training and prediction                   | Complete    |
| Practise a feature-branch and pull-request workflow               | Complete    |
| Complete the README and Git recovery guide                        | In progress |
| Convert the code into an installable Python package               | Planned     |
| Create a consistent command-line interface                        | Planned     |
| Extract and test pure Elo functions                               | Planned     |
| Refactor and validate the data pipeline                           | Planned     |
| Implement leak-free chronological evaluation                      | Planned     |
| Compare Elo against a constant-probability baseline               | Planned     |
| Export predictions, rankings and evaluation metrics               | Planned     |
| Add automated tests and GitHub Actions                            | Planned     |
| Produce charts and a results discussion                           | Planned     |
| Test the project from a clean clone and release version 1.0       | Planned     |

## Version 1.0 Definition of Done

Version 1.0 will be considered complete when:

* A clean clone can install the project using documented instructions.
* One command can prepare the data reproducibly.
* One command can reproduce the main evaluation.
* Matches are evaluated chronologically without future-information leakage.
* Elo results are compared with a simple baseline.
* Predictions, rankings and metrics are exported.
* At least five meaningful automated tests pass.
* GitHub Actions runs the tests automatically.
* The README explains the method, results and limitations.
* Another person can reproduce the main result without private instructions.

## Licence

See [LICENSE](LICENSE) for the software licence.

The cricket data belongs to its respective publishers and is subject to Cricsheet's separate terms and attribution requirements.
