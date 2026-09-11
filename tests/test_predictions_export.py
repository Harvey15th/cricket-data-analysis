import csv
import math
import subprocess
import sys

import pytest


MATCH_DETAILS = ("match_id", "date", "team1", "team2", "result")
MATCH_FIELDS = [*MATCH_DETAILS, "match_type"]
PREDICTION_FIELDS = {
    *MATCH_DETAILS,
    "elo_team1_before",
    "elo_team2_before",
    "p_team1",
    "actual_score",
    "status",
    "elo_brier",
    "baseline_brier",
}
SCORE_FIELDS = ("brier_score", "baseline_brier_score", "brier_improvement")
SUMMARY_FIELDS = {
    *SCORE_FIELDS,
    "matches_evaluated",
    "matches_skipped",
    "training_end",
    "verification_start",
}

# Independent fixture values, not imported from the application under test.
P_AFTER_ALPHA_WIN = 0.6400649998028851
P_AFTER_ALPHA_WIN_THEN_TIE = 0.6021401655765967
ALPHA_ELO_AFTER_WIN_THEN_TIE = 1535.9935000197115
BETA_ELO_AFTER_WIN_THEN_TIE = 1464.0064999802885


def match(match_id, date, team1="Alpha", team2="Beta", result="Alpha"):
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


def run_benchmark(tmp_path, training, verification, *, export_predictions=True):
    """Run the installed package, independently of the repository's cwd."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    training_path = tmp_path / "training.csv"
    verification_path = tmp_path / "verification.csv"
    summary_path = tmp_path / "evaluation.csv"
    predictions_path = tmp_path / "predictions.csv"
    write_matches(training_path, training)
    write_matches(verification_path, verification)

    command = [
        sys.executable,
        "-m",
        "cricket_elo",
        "benchmark",
        "--training-data",
        str(training_path),
        "--verification-data",
        str(verification_path),
        "--output",
        str(summary_path),
    ]
    if export_predictions:
        command.extend(["--predictions-output", str(predictions_path)])

    result = subprocess.run(
        command,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result, summary_path, predictions_path


def assert_success(result):
    assert result.returncode == 0, (
        f"Benchmark exited with {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def read_csv(path, required_fields):
    assert path.is_file(), f"Expected output file was not created: {path.name}"
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing = required_fields - set(reader.fieldnames or [])
        assert not missing, f"{path.name} is missing columns: {sorted(missing)}"
        rows = list(reader)

    for row in rows:
        assert None not in row, f"{path.name} contains a row with too many cells."
        assert all(row[field] is not None for field in required_fields), (
            f"{path.name} contains a row with missing cells: {row}"
        )
    return rows


def read_summary(path):
    rows = read_csv(path, SUMMARY_FIELDS)
    assert len(rows) == 1, "Expected exactly one evaluation summary row."
    summary = rows[0]
    for field in SCORE_FIELDS:
        summary[field] = float(summary[field])
        assert math.isfinite(summary[field]), f"{field} must be finite."
    for field in ("matches_evaluated", "matches_skipped"):
        summary[field] = int(summary[field])
    return summary


def read_successful_export(result, summary_path, predictions_path):
    assert_success(result)
    return read_summary(summary_path), read_csv(predictions_path, PREDICTION_FIELDS)


def test_export_contains_every_verification_match_once_in_order(tmp_path):
    training = [match("001", "2026-01-01")]
    verification = [
        match("002", "2026-02-01"),
        match("003", "2026-02-01", result="tie"),
        match("004", "2026-02-02", result="no result"),
        match("005", "2026-02-03", result="Beta"),
    ]
    _, rows = read_successful_export(*run_benchmark(tmp_path, training, verification))

    # Compare all identifying details, including order within the same date.
    assert [tuple(row[field] for field in MATCH_DETAILS) for row in rows] == [
        tuple(row[field] for field in MATCH_DETAILS) for row in verification
    ]
    assert [row["status"] for row in rows] == [
        "evaluated", "tie", "no_result", "evaluated"
    ]
    assert float(rows[0]["actual_score"]) == 1.0
    assert float(rows[1]["actual_score"]) == 0.5
    assert rows[2]["actual_score"] == ""
    assert float(rows[3]["actual_score"]) == 0.0


@pytest.mark.parametrize("second_winner", ["Alpha", "Beta"])
def test_export_uses_pre_match_ratings_and_team1_perspective(tmp_path, second_winner):
    # Alpha and Beta are new teams. Swapping their positions in the second
    # match checks that p_team1 always refers to the first named team.
    training = [match("001", "2026-01-01", "Gamma", "Delta", "Gamma")]
    verification = [
        match("002", "2026-02-01"),
        match("003", "2026-02-02", "Beta", "Alpha", second_winner),
    ]
    _, rows = read_successful_export(*run_benchmark(tmp_path, training, verification))
    assert len(rows) == 2
    first, second = rows

    assert float(first["elo_team1_before"]) == pytest.approx(1500.0)
    assert float(first["elo_team2_before"]) == pytest.approx(1500.0)
    assert float(first["p_team1"]) == pytest.approx(0.5)
    assert float(first["elo_brier"]) == pytest.approx(0.25)

    assert float(second["elo_team1_before"]) == pytest.approx(1450.0)
    assert float(second["elo_team2_before"]) == pytest.approx(1550.0)
    expected_p = 1 - P_AFTER_ALPHA_WIN
    expected_score = 1.0 if second_winner == "Beta" else 0.0
    assert float(second["p_team1"]) == pytest.approx(expected_p)
    assert float(second["actual_score"]) == expected_score
    assert float(second["elo_brier"]) == pytest.approx((expected_score - expected_p) ** 2)
    assert float(second["baseline_brier"]) == pytest.approx(0.25)


def test_tie_updates_ratings_and_no_result_leaves_them_unchanged(tmp_path):
    training = [match("001", "2026-01-01")]
    verification = [
        match("002", "2026-02-01", result="no result"),
        match("003", "2026-02-02", result="tie"),
        match("004", "2026-02-03"),
    ]
    summary, rows = read_successful_export(*run_benchmark(tmp_path, training, verification))
    assert len(rows) == 3

    for row, expected_status in zip(rows[:2], ("no_result", "tie")):
        assert row["status"] == expected_status
        assert float(row["elo_team1_before"]) == pytest.approx(1550.0)
        assert float(row["elo_team2_before"]) == pytest.approx(1450.0)
        assert float(row["p_team1"]) == pytest.approx(P_AFTER_ALPHA_WIN)
        assert row["elo_brier"] == "", "Skipped matches must have blank Brier cells."
        assert row["baseline_brier"] == ""

    last = rows[2]
    assert float(last["elo_team1_before"]) == pytest.approx(ALPHA_ELO_AFTER_WIN_THEN_TIE)
    assert float(last["elo_team2_before"]) == pytest.approx(BETA_ELO_AFTER_WIN_THEN_TIE)
    assert float(last["p_team1"]) == pytest.approx(P_AFTER_ALPHA_WIN_THEN_TIE)
    assert float(last["elo_brier"]) == pytest.approx(0.15829244784741792)
    assert summary["brier_score"] == pytest.approx(0.15829244784741792)
    assert summary["matches_evaluated"] == 1
    assert summary["matches_skipped"] == 2


@pytest.mark.parametrize(
    "warmup_result, expected_a, expected_b",
    [
        pytest.param("no result", 1550.0, 1450.0, id="no-result-does-not-count"),
        pytest.param("tie", 1532.0, 1468.0, id="tie-counts-towards-k-threshold"),
    ],
)
def test_export_preserves_match_counts_at_k_threshold(
    tmp_path, warmup_result, expected_a, expected_b
):
    # Six training ties leave both ratings at 1500 and both match counts at 6.
    # A further tie moves counts to 7; a no-result leaves them at 6. The next
    # win therefore uses K=64 or K=100, visible in the following exported row.
    training = [
        match(f"{i:03}", f"2026-01-{i:02}", result="tie")
        for i in range(1, 7)
    ]
    verification = [
        match("007", "2026-02-01", result=warmup_result),
        match("008", "2026-02-02"),
        match("009", "2026-02-03", result="Beta"),
    ]
    _, rows = read_successful_export(*run_benchmark(tmp_path, training, verification))
    assert len(rows) == 3
    assert float(rows[1]["p_team1"]) == pytest.approx(0.5)
    assert float(rows[2]["elo_team1_before"]) == pytest.approx(expected_a)
    assert float(rows[2]["elo_team2_before"]) == pytest.approx(expected_b)
    expected_p = 1 / (1 + 10 ** ((expected_b - expected_a) / 400))
    assert float(rows[2]["p_team1"]) == pytest.approx(expected_p)


def test_exported_errors_and_counts_reproduce_summary(tmp_path):
    training = [match("001", "2026-01-01")]
    verification = [
        match("002", "2026-02-01"),
        match("003", "2026-02-02", "Beta", "Alpha", "Alpha"),
        match("004", "2026-02-03", result="tie"),
        match("005", "2026-02-04", result="no result"),
        match("006", "2026-02-05", result="Beta"),
    ]
    summary, rows = read_successful_export(*run_benchmark(tmp_path, training, verification))
    evaluated = [row for row in rows if row["status"] == "evaluated"]
    skipped = [row for row in rows if row["status"] in {"tie", "no_result"}]
    assert len(evaluated) == 3
    assert len(skipped) == 2
    assert len(rows) == len(evaluated) + len(skipped)
    assert summary["matches_evaluated"] == len(evaluated)
    assert summary["matches_skipped"] == len(skipped)
    assert summary["training_end"] == training[-1]["date"]
    assert summary["verification_start"] == verification[0]["date"]

    for row in evaluated:
        probability = float(row["p_team1"])
        score = float(row["actual_score"])
        expected_score = 1.0 if row["result"] == row["team1"] else 0.0
        assert 0.0 <= probability <= 1.0
        assert score == expected_score
        assert float(row["elo_brier"]) == pytest.approx((score - probability) ** 2)
        assert float(row["baseline_brier"]) == pytest.approx(0.25)

    for row in skipped:
        assert row["elo_brier"] == ""
        assert row["baseline_brier"] == ""

    elo_mean = math.fsum(float(row["elo_brier"]) for row in evaluated) / len(evaluated)
    baseline_mean = math.fsum(float(row["baseline_brier"]) for row in evaluated) / len(evaluated)
    assert summary["brier_score"] == pytest.approx(elo_mean)
    assert summary["baseline_brier_score"] == pytest.approx(baseline_mean)
    assert summary["brier_improvement"] == pytest.approx(baseline_mean - elo_mean)


def test_predictions_export_is_optional_and_does_not_change_summary(tmp_path):
    training = [match("001", "2026-01-01")]
    verification = [
        match("002", "2026-02-01", result="tie"),
        match("003", "2026-02-02"),
        match("004", "2026-02-03", result="Beta"),
    ]
    with_export, _ = read_successful_export(
        *run_benchmark(tmp_path / "with export", training, verification)
    )
    result, summary_path, predictions_path = run_benchmark(
        tmp_path / "without export", training, verification, export_predictions=False
    )
    assert_success(result)
    without_export = read_summary(summary_path)
    assert not predictions_path.exists(), "Export should be opt-in."

    for field in SUMMARY_FIELDS:
        if field in SCORE_FIELDS:
            assert without_export[field] == pytest.approx(with_export[field])
        else:
            assert without_export[field] == with_export[field]


def test_repeated_export_replaces_previous_rows(tmp_path):
    training = [match("001", "2026-01-01")]
    verification = [
        match("002", "2026-02-01"),
        match("003", "2026-02-02", result="Beta"),
    ]
    _, first_rows = read_successful_export(*run_benchmark(tmp_path, training, verification))
    assert len(first_rows) == 2

    # Reuse the same output paths with fewer input matches. Old rows must not
    # remain, and the new run starts from the training state again.
    summary, rows = read_successful_export(
        *run_benchmark(tmp_path, training, verification[1:])
    )
    assert len(rows) == 1
    assert rows[0]["match_id"] == "003"
    assert float(rows[0]["p_team1"]) == pytest.approx(P_AFTER_ALPHA_WIN)
    assert summary["matches_evaluated"] == 1
    assert summary["brier_score"] == pytest.approx(P_AFTER_ALPHA_WIN ** 2)


@pytest.mark.parametrize(
    "verification",
    [
        pytest.param(
            [match("003", "2026-02-02"), match("002", "2026-02-01")],
            id="unsorted-verification",
        ),
        pytest.param(
            [match("001", "2026-02-01")],
            id="match-id-overlaps-training",
        ),
        pytest.param([], id="empty-verification"),
        pytest.param(
            [
                match("002", "2026-02-01", result="tie"),
                match("003", "2026-02-02", result="no result"),
            ],
            id="no-decisive-matches",
        ),
    ],
)
def test_failed_evaluation_creates_neither_output(tmp_path, verification):
    result, summary_path, predictions_path = run_benchmark(
        tmp_path, [match("001", "2026-01-01")], verification
    )
    assert result.returncode == 1, (
        f"Expected a handled evaluation failure, got exit {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "Traceback" not in result.stderr, result.stderr
    assert not summary_path.exists(), "Failed evaluation created a summary report."
    assert not predictions_path.exists(), "Failed evaluation created a prediction report."