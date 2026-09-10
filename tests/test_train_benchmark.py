import subprocess
import sys
import pytest


def run_cli(working_directory, *arguments):
    """Run cricket-elo as a user would run it from the terminal."""
    return subprocess.run(
        [sys.executable, "-m", "cricket_elo", *map(str, arguments)],
        cwd=working_directory,
        capture_output=True,
        text=True,
    )


def write_matches(path, rows):
    """Create a tiny processed-match CSV fixture."""
    lines = [",".join(row) for row in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_ratings(path):
    """Read the generated ratings into a convenient dictionary."""
    ratings = {}

    for line in path.read_text(encoding="utf-8").splitlines():
        team_name, rating, matches_played = line.split(",")

        ratings[team_name] = {
            "rating": float(rating),
            "matches_played": int(matches_played),
        }

    return ratings


def test_training_one_team_a_win(tmp_path):
    training_data = tmp_path / "training.csv"
    output_file = tmp_path / "ratings.csv"

    write_matches(
        training_data,
        [
            ["001", "2026-01-01", "Alpha", "Beta", "Alpha", "T20"],
        ],
    )

    result = run_cli(
        tmp_path,
        "train",
        "--input-data",
        training_data,
        "--output",
        output_file,
    )

    assert result.returncode == 0, result.stderr

    ratings = read_ratings(output_file)

    assert ratings["Alpha"]["rating"] == pytest.approx(1550)
    assert ratings["Beta"]["rating"] == pytest.approx(1450)
    assert ratings["Alpha"]["matches_played"] == 1
    assert ratings["Beta"]["matches_played"] == 1


def test_training_no_result_changes_nothing(tmp_path):
    training_data = tmp_path / "training.csv"
    output_file = tmp_path / "ratings.csv"

    write_matches(
        training_data,
        [
            ["001", "2026-01-01", "Alpha", "Beta", "no result", "T20"],
        ],
    )

    result = run_cli(
        tmp_path,
        "train",
        "--input-data",
        training_data,
        "--output",
        output_file,
    )

    assert result.returncode == 0, result.stderr

    ratings = read_ratings(output_file)

    assert ratings["Alpha"]["rating"] == pytest.approx(1500)
    assert ratings["Beta"]["rating"] == pytest.approx(1500)
    assert ratings["Alpha"]["matches_played"] == 0
    assert ratings["Beta"]["matches_played"] == 0


def test_benchmark_trains_then_evaluates_new_match(tmp_path):
    training_data = tmp_path / "training.csv"
    verification_data = tmp_path / "verification.csv"

    # benchmark.py currently writes this file to a fixed outputs directory.
    (tmp_path / "outputs").mkdir()

    write_matches(
        training_data,
        [
            ["001", "2026-01-01", "Alpha", "Beta", "Alpha", "T20"],
        ],
    )

    write_matches(
        verification_data,
        [
            ["002", "2026-02-01", "Alpha", "Beta", "Alpha", "T20"],
        ],
    )

    result = run_cli(
        tmp_path,
        "benchmark",
        "--training-data",
        training_data,
        "--verification-data",
        verification_data,
    )

    assert result.returncode == 0, result.stderr

    metric_line = next(
        line
        for line in result.stdout.splitlines()
        if line.startswith("Square Error is ")
    )
    measured_error = float(metric_line.removeprefix("Square Error is "))

    # Training produces ratings of 1550 and 1450.
    # Their next-match expected score is approximately 0.640065.
    expected_error = (1 - 0.6400649998028851) ** 2

    assert measured_error == pytest.approx(expected_error)