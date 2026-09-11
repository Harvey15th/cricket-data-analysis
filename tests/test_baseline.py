import csv
import subprocess
import sys

import pytest


MATCH_FIELDS = ["match_id", "date", "team1", "team2", "result", "match_type"]
SUMMARY_FIELDS = {
    "brier_score",
    "baseline_brier_score",
    "brier_improvement",
    "matches_evaluated",
    "matches_skipped",
    "training_end",
    "verification_start",
}

# Independently calculated for these fixtures: after Alpha beats Beta once,
# ratings are 1550 and 1450, so Alpha's next expected score is this number.
ALPHA_AFTER_ONE_WIN = 0.6400649998028851


def match(match_id, date, team1, team2, result):
    return {
        "match_id": match_id,
        "date": date,
        "team1": team1,
        "team2": team2,
        "result": result,
        "match_type": "T20",
    }


def write_matches(path, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=MATCH_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run_benchmark(tmp_path, training_rows, verification_rows):
    """Write two CSV fixtures and invoke the installed Cricket Elo package."""
    training_path = tmp_path / "training.csv"
    verification_path = tmp_path / "verification.csv"
    output_path = tmp_path / "evaluation.csv"
    write_matches(training_path, training_rows)
    write_matches(verification_path, verification_rows)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cricket_elo",
            "benchmark",
            "--training-data",
            str(training_path),
            "--verification-data",
            str(verification_path),
            "--output",
            str(output_path),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result, output_path


def read_successful_summary(result, output_path):
    """Check command success and read one summary row with numeric values."""
    assert result.returncode == 0, (
        f"Benchmark exited with {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert output_path.is_file(), "Benchmark did not create its evaluation CSV."

    with output_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing = SUMMARY_FIELDS - set(reader.fieldnames or [])
        assert not missing, f"Missing evaluation fields: {sorted(missing)}"
        rows = list(reader)

    assert len(rows) == 1, "Expected exactly one evaluation summary row."
    summary = rows[0]
    for field in ("brier_score", "baseline_brier_score", "brier_improvement"):
        summary[field] = float(summary[field])
    for field in ("matches_evaluated", "matches_skipped"):
        summary[field] = int(summary[field])
    return summary


@pytest.mark.parametrize("winner", ["Alpha", "Beta"])
def test_equal_ratings_match_the_baseline(tmp_path, winner):
    # Unrelated training teams leave Alpha and Beta at their initial ratings.
    result, output = run_benchmark(
        tmp_path,
        [match("001", "2026-01-01", "Gamma", "Delta", "Gamma")],
        [match("002", "2026-02-01", "Alpha", "Beta", winner)],
    )
    summary = read_successful_summary(result, output)

    assert summary["brier_score"] == pytest.approx(0.25)
    assert summary["baseline_brier_score"] == pytest.approx(0.25)
    assert summary["brier_improvement"] == pytest.approx(0.0)
    assert summary["matches_evaluated"] == 1
    assert summary["matches_skipped"] == 0
    assert summary["training_end"] == "2026-01-01"
    assert summary["verification_start"] == "2026-02-01"


@pytest.mark.parametrize(
    "winner, expected_elo_brier",
    [
        pytest.param(
            "Alpha", (1 - ALPHA_AFTER_ONE_WIN) ** 2, id="higher-rated-team-wins"
        ),
        pytest.param(
            "Beta", ALPHA_AFTER_ONE_WIN ** 2, id="lower-rated-team-wins"
        ),
    ],
)
def test_comparison_can_show_positive_or_negative_improvement(
    tmp_path, winner, expected_elo_brier
):
    result, output = run_benchmark(
        tmp_path,
        [match("001", "2026-01-01", "Alpha", "Beta", "Alpha")],
        [match("002", "2026-02-01", "Alpha", "Beta", winner)],
    )
    summary = read_successful_summary(result, output)

    # Alpha's win improves on 0.25; Beta's win makes Elo worse than 0.25.
    # Negative improvement is a legitimate evaluation result.
    assert summary["brier_score"] == pytest.approx(expected_elo_brier)
    assert summary["baseline_brier_score"] == pytest.approx(0.25)
    assert summary["brier_improvement"] == pytest.approx(0.25 - expected_elo_brier)
    assert summary["matches_evaluated"] == 1
    assert summary["matches_skipped"] == 0


def test_both_metrics_exclude_ties_and_no_results(tmp_path):
    result, output = run_benchmark(
        tmp_path,
        [match("001", "2026-01-01", "Alpha", "Beta", "Alpha")],
        [
            match("002", "2026-02-01", "Alpha", "Beta", "no result"),
            match("003", "2026-02-02", "Alpha", "Beta", "tie"),
            match("004", "2026-02-03", "Alpha", "Beta", "Alpha"),
        ],
    )
    summary = read_successful_summary(result, output)

    # The no-result changes nothing. The tie moves the ratings from 1550/1450
    # to approximately 1535.9935/1464.0065. Only the last match is scored.
    expected_elo_brier = 0.15829244784741792
    assert summary["brier_score"] == pytest.approx(expected_elo_brier)
    assert summary["baseline_brier_score"] == pytest.approx(0.25)
    assert summary["brier_improvement"] == pytest.approx(0.25 - expected_elo_brier)
    assert summary["matches_evaluated"] == 1
    assert summary["matches_skipped"] == 2
    # The verification period starts at its first record, even if unscored.
    assert summary["verification_start"] == "2026-02-01"


def test_brier_scores_average_all_decisive_verification_matches(tmp_path):
    result, output = run_benchmark(
        tmp_path,
        [match("001", "2026-01-01", "Gamma", "Delta", "Gamma")],
        [
            match("002", "2026-02-01", "Alpha", "Beta", "Alpha"),
            match("003", "2026-02-02", "Alpha", "Beta", "Beta"),
        ],
    )
    summary = read_successful_summary(result, output)

    # First prediction: 0.5. Second: about 0.640065 for Alpha, but Beta wins.
    # This checks sequential updates and averaging over the entire period.
    expected_elo_brier = (0.25 + ALPHA_AFTER_ONE_WIN ** 2) / 2
    assert summary["brier_score"] == pytest.approx(expected_elo_brier)
    assert summary["baseline_brier_score"] == pytest.approx(0.25)
    assert summary["brier_improvement"] == pytest.approx(0.25 - expected_elo_brier)
    assert summary["matches_evaluated"] == 2
    assert summary["matches_skipped"] == 0


def test_no_decisive_matches_produces_no_baseline_score(tmp_path):
    result, output = run_benchmark(
        tmp_path,
        [match("001", "2026-01-01", "Alpha", "Beta", "Alpha")],
        [
            match("002", "2026-02-01", "Alpha", "Beta", "tie"),
            match("003", "2026-02-02", "Alpha", "Beta", "no result"),
        ],
    )

    assert result.returncode == 1, (
        f"Expected a handled evaluation failure.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "Traceback" not in result.stderr, result.stderr
    assert not output.exists(), "An empty evaluation must not report a Brier score."
