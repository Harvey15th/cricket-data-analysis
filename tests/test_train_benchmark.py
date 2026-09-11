import csv
import json
import subprocess
import sys

import pytest


MATCH_FIELDS = ["match_id", "date", "team1", "team2", "result", "match_type"]
RATING_FIELDS = ["name", "elo", "matches_played"]


def run_cli(working_directory, *arguments):
    """Run Cricket Elo using the same interpreter that is running pytest."""
    return subprocess.run(
        [sys.executable, "-m", "cricket_elo", *map(str, arguments)],
        cwd=working_directory,
        capture_output=True,
        text=True,
    )


def write_cricsheet_match(
    directory,
    match_id,
    date,
    team1,
    team2,
    outcome,
):
    """Write the smallest Cricsheet-shaped JSON document needed by prepare."""
    match = {
        "info": {
            "dates": [date],
            "teams": [team1, team2],
            "match_type": "T20",
            "outcome": outcome,
        }
    }

    filepath = directory / f"{match_id}.json"
    filepath.write_text(json.dumps(match), encoding="utf-8")


def read_csv(path):
    """Return a CSV file's field names and rows."""
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return reader.fieldnames, list(reader)


def read_ratings(path):
    """Load a ratings CSV and convert its numeric fields at the test boundary."""
    fieldnames, rows = read_csv(path)
    assert fieldnames == RATING_FIELDS

    return {
        row["name"]: {
            "elo": float(row["elo"]),
            "matches_played": int(row["matches_played"]),
        }
        for row in rows
    }


def prepare_matches(working_directory, raw_directory, output_path):
    """Run preparation and include stderr in the assertion on failure."""
    result = run_cli(
        working_directory,
        "prepare",
        "--input",
        raw_directory,
        "--output",
        output_path,
    )

    assert result.returncode == 0, result.stderr
    return result


def test_prepare_writes_header_and_deterministic_order(tmp_path):
    raw_directory = tmp_path / "raw"
    raw_directory.mkdir()
    output_path = tmp_path / "matches.csv"

    # Deliberately create these in an order different from the required output.
    write_cricsheet_match(
        raw_directory,
        "200",
        "2026-02-01",
        "Alpha",
        "Beta",
        {"winner": "Alpha"},
    )
    write_cricsheet_match(
        raw_directory,
        "102",
        "2026-01-01",
        "Gamma",
        "Delta",
        {"winner": "Delta"},
    )
    write_cricsheet_match(
        raw_directory,
        "101",
        "2026-01-01",
        "Epsilon",
        "Zeta",
        {"winner": "Epsilon"},
    )
    (raw_directory / "notes.txt").write_text("not match data", encoding="utf-8")

    prepare_matches(tmp_path, raw_directory, output_path)

    fieldnames, rows = read_csv(output_path)

    assert fieldnames == MATCH_FIELDS
    assert [row["match_id"] for row in rows] == ["101", "102", "200"]


def test_prepare_normalises_tie_and_no_result(tmp_path):
    raw_directory = tmp_path / "raw"
    raw_directory.mkdir()
    output_path = tmp_path / "matches.csv"

    write_cricsheet_match(
        raw_directory,
        "001",
        "2026-01-01",
        "Alpha",
        "Beta",
        {"result": "tie"},
    )
    write_cricsheet_match(
        raw_directory,
        "002",
        "2026-01-02",
        "Alpha",
        "Beta",
        {"result": "no result"},
    )

    prepare_matches(tmp_path, raw_directory, output_path)
    _, rows = read_csv(output_path)

    assert [row["result"] for row in rows] == ["tie", "no result"]


def test_prepare_overwrites_instead_of_duplicating_output(tmp_path):
    raw_directory = tmp_path / "raw"
    raw_directory.mkdir()
    output_path = tmp_path / "matches.csv"

    write_cricsheet_match(
        raw_directory,
        "001",
        "2026-01-01",
        "Alpha",
        "Beta",
        {"winner": "Alpha"},
    )

    prepare_matches(tmp_path, raw_directory, output_path)
    first_output = output_path.read_text(encoding="utf-8")

    prepare_matches(tmp_path, raw_directory, output_path)
    second_output = output_path.read_text(encoding="utf-8")

    _, rows = read_csv(output_path)
    assert second_output == first_output
    assert len(rows) == 1


def test_prepare_rejects_winner_that_did_not_play(tmp_path):
    raw_directory = tmp_path / "raw"
    raw_directory.mkdir()
    output_path = tmp_path / "matches.csv"

    write_cricsheet_match(
        raw_directory,
        "001",
        "2026-01-01",
        "Alpha",
        "Beta",
        {"winner": "Gamma"},
    )

    result = run_cli(
        tmp_path,
        "prepare",
        "--input",
        raw_directory,
        "--output",
        output_path,
    )

    assert result.returncode != 0


def test_prepared_data_can_be_trained_and_no_result_is_skipped(tmp_path):
    raw_directory = tmp_path / "raw"
    raw_directory.mkdir()
    matches_path = tmp_path / "matches.csv"
    ratings_path = tmp_path / "ratings.csv"

    write_cricsheet_match(
        raw_directory,
        "001",
        "2026-01-01",
        "Alpha",
        "Beta",
        {"winner": "Alpha"},
    )
    write_cricsheet_match(
        raw_directory,
        "002",
        "2026-01-02",
        "Alpha",
        "Beta",
        {"result": "no result"},
    )

    prepare_matches(tmp_path, raw_directory, matches_path)

    result = run_cli(
        tmp_path,
        "train",
        "--input-data",
        matches_path,
        "--output",
        ratings_path,
    )

    assert result.returncode == 0, result.stderr

    ratings = read_ratings(ratings_path)
    assert ratings["Alpha"]["elo"] == pytest.approx(1550)
    assert ratings["Beta"]["elo"] == pytest.approx(1450)
    assert ratings["Alpha"]["matches_played"] == 1
    assert ratings["Beta"]["matches_played"] == 1


def test_prediction_can_use_generated_ratings(tmp_path):
    raw_directory = tmp_path / "raw"
    raw_directory.mkdir()
    matches_path = tmp_path / "matches.csv"
    ratings_path = tmp_path / "ratings.csv"

    write_cricsheet_match(
        raw_directory,
        "001",
        "2026-01-01",
        "Alpha",
        "Beta",
        {"winner": "Alpha"},
    )

    prepare_matches(tmp_path, raw_directory, matches_path)
    training_result = run_cli(
        tmp_path,
        "train",
        "--input-data",
        matches_path,
        "--output",
        ratings_path,
    )
    assert training_result.returncode == 0, training_result.stderr

    prediction_result = run_cli(
        tmp_path,
        "predict",
        "--ratings",
        ratings_path,
        "--team-a",
        "Alpha",
        "--team-b",
        "Beta",
    )

    assert prediction_result.returncode == 0, prediction_result.stderr
    assert "Alpha has a 64% chance of winning" in prediction_result.stdout


def test_benchmark_trains_then_scores_a_later_match(tmp_path):
    training_raw = tmp_path / "training_raw"
    verification_raw = tmp_path / "verification_raw"
    training_raw.mkdir()
    verification_raw.mkdir()

    training_data = tmp_path / "training.csv"
    verification_data = tmp_path / "verification.csv"
    evaluation_path = tmp_path / "evaluation.csv"

    write_cricsheet_match(
        training_raw,
        "001",
        "2026-01-01",
        "Alpha",
        "Beta",
        {"winner": "Alpha"},
    )
    write_cricsheet_match(
        verification_raw,
        "002",
        "2026-02-01",
        "Alpha",
        "Beta",
        {"winner": "Alpha"},
    )

    prepare_matches(tmp_path, training_raw, training_data)
    prepare_matches(tmp_path, verification_raw, verification_data)

    result = run_cli(
        tmp_path,
        "benchmark",
        "--training-data",
        training_data,
        "--verification-data",
        verification_data,
        "--output",
        evaluation_path,
    )

    assert result.returncode == 0, result.stderr
    assert evaluation_path.is_file(), "Benchmark did not create its evaluation CSV."

    fieldnames, rows = read_csv(evaluation_path)
    required_fields = {
        "brier_score",
        "matches_evaluated",
        "matches_skipped",
        "training_end",
        "verification_start",
    }
    assert required_fields.issubset(set(fieldnames or []))
    assert len(rows) == 1, "Expected one evaluation summary row."
    evaluation = rows[0]

    # Training leaves Alpha at 1550 and Beta at 1450. The verification
    # prediction is therefore approximately 0.640065 for Alpha.
    expected_error = (1 - 0.6400649998028851) ** 2
    assert float(evaluation["brier_score"]) == pytest.approx(expected_error)
    assert int(evaluation["matches_evaluated"]) == 1
    assert int(evaluation["matches_skipped"]) == 0
    assert evaluation["training_end"] == "2026-01-01"
    assert evaluation["verification_start"] == "2026-02-01"
