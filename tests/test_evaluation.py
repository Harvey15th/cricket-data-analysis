"""Integration tests for leak-free chronological Elo evaluation."""

import csv

import pytest

from cricket_elo.benchmark import benchmark, verify_data


MATCH_FIELDS = ["match_id", "date", "team1", "team2", "result", "match_type"]
REQUIRED_EVALUATION_FIELDS = {
    "brier_score",
    "matches_evaluated",
    "matches_skipped",
    "training_end",
    "verification_start",
}


def match(match_id, date, team1, team2, result):
    """Create one processed match row."""
    return {
        "match_id": match_id,
        "date": date,
        "team1": team1,
        "team2": team2,
        "result": result,
        "match_type": "T20",
    }


def write_matches(path, rows):
    """Write processed matches in exactly the supplied order."""
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=MATCH_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def read_evaluation(path):
    """Read and validate the single-row evaluation summary."""
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    assert len(rows) == 1
    assert REQUIRED_EVALUATION_FIELDS.issubset(rows[0])
    return rows[0]


def test_verify_data_accepts_one_later_verification_match(tmp_path):
    training_data = tmp_path / "training.csv"
    verification_data = tmp_path / "verification.csv"

    write_matches(
        training_data,
        [match("001", "2026-01-01", "Alpha", "Beta", "Alpha")],
    )
    write_matches(
        verification_data,
        [match("002", "2026-02-01", "Alpha", "Beta", "Beta")],
    )

    teams, matches, is_valid, training_end, verification_start = verify_data(
        training_data,
        verification_data,
    )

    assert is_valid is True
    assert set(teams) == {"Alpha", "Beta"}
    assert len(matches) == 1
    assert training_end == "2026-01-01"
    assert verification_start == "2026-02-01"


def test_verify_data_rejects_unsorted_verification_matches(tmp_path):
    training_data = tmp_path / "training.csv"
    verification_data = tmp_path / "verification.csv"

    write_matches(
        training_data,
        [match("001", "2026-01-01", "Alpha", "Beta", "Alpha")],
    )
    write_matches(
        verification_data,
        [
            match("003", "2026-03-01", "Alpha", "Beta", "Alpha"),
            match("002", "2026-02-01", "Alpha", "Beta", "Beta"),
        ],
    )

    _, _, is_valid, _, _ = verify_data(training_data, verification_data)

    assert is_valid is False


def test_verify_data_rejects_duplicate_match_ids_across_files(tmp_path):
    training_data = tmp_path / "training.csv"
    verification_data = tmp_path / "verification.csv"

    write_matches(
        training_data,
        [match("001", "2026-01-01", "Alpha", "Beta", "Alpha")],
    )
    write_matches(
        verification_data,
        [match("001", "2026-02-01", "Alpha", "Beta", "Beta")],
    )

    _, _, is_valid, _, _ = verify_data(training_data, verification_data)

    assert is_valid is False


def test_verify_data_uses_date_and_match_id_at_period_boundary(tmp_path):
    training_data = tmp_path / "training.csv"
    verification_data = tmp_path / "verification.csv"

    # The dates are equal, but verification match 100 precedes training match
    # 200 under the project's (date, match_id) chronological ordering.
    write_matches(
        training_data,
        [match("200", "2026-02-01", "Alpha", "Beta", "Alpha")],
    )
    write_matches(
        verification_data,
        [match("100", "2026-02-01", "Alpha", "Beta", "Beta")],
    )

    _, _, is_valid, _, _ = verify_data(training_data, verification_data)

    assert is_valid is False


def test_benchmark_scores_first_prediction_before_updating(tmp_path):
    training_data = tmp_path / "training.csv"
    verification_data = tmp_path / "verification.csv"
    output_path = tmp_path / "evaluation.csv"

    # The training teams are deliberately unrelated. Alpha and Beta therefore
    # enter verification at equal ratings and must receive a 0.5 prediction.
    write_matches(
        training_data,
        [match("001", "2026-01-01", "Gamma", "Delta", "Gamma")],
    )
    write_matches(
        verification_data,
        [match("002", "2026-02-01", "Alpha", "Beta", "Alpha")],
    )

    result = benchmark(training_data, verification_data, output_path)

    assert result is True
    evaluation = read_evaluation(output_path)
    assert float(evaluation["brier_score"]) == pytest.approx(0.25)
    assert int(evaluation["matches_evaluated"]) == 1
    assert int(evaluation["matches_skipped"]) == 0
    assert evaluation["training_end"] == "2026-01-01"
    assert evaluation["verification_start"] == "2026-02-01"


def test_no_result_is_excluded_from_denominator_and_rating_state(tmp_path):
    training_data = tmp_path / "training.csv"
    verification_data = tmp_path / "verification.csv"
    output_path = tmp_path / "evaluation.csv"

    write_matches(
        training_data,
        [match("001", "2026-01-01", "Alpha", "Beta", "Alpha")],
    )
    write_matches(
        verification_data,
        [
            match("002", "2026-02-01", "Alpha", "Beta", "no result"),
            match("003", "2026-03-01", "Alpha", "Beta", "Alpha"),
        ],
    )

    result = benchmark(training_data, verification_data, output_path)

    assert result is True
    evaluation = read_evaluation(output_path)

    # Training moves the ratings to 1550 and 1450. A no-result must leave that
    # state unchanged before the following decisive match is predicted.
    probability = 1 / (1 + 10 ** ((1450 - 1550) / 400))
    expected_brier = (1 - probability) ** 2

    assert float(evaluation["brier_score"]) == pytest.approx(expected_brier)
    assert int(evaluation["matches_evaluated"]) == 1
    assert int(evaluation["matches_skipped"]) == 1


def test_tie_updates_ratings_but_is_excluded_from_binary_metric(tmp_path):
    training_data = tmp_path / "training.csv"
    verification_data = tmp_path / "verification.csv"
    output_path = tmp_path / "evaluation.csv"

    write_matches(
        training_data,
        [match("001", "2026-01-01", "Alpha", "Beta", "Alpha")],
    )
    write_matches(
        verification_data,
        [
            match("002", "2026-02-01", "Alpha", "Beta", "tie"),
            match("003", "2026-03-01", "Alpha", "Beta", "Alpha"),
        ],
    )

    result = benchmark(training_data, verification_data, output_path)

    assert result is True
    evaluation = read_evaluation(output_path)

    probability_before_tie = 1 / (1 + 10 ** ((1450 - 1550) / 400))
    rating_error = 0.5 - probability_before_tie
    alpha_after_tie = 1550 + 100 * rating_error
    beta_after_tie = 1450 - 100 * rating_error
    probability_after_tie = 1 / (
        1 + 10 ** ((beta_after_tie - alpha_after_tie) / 400)
    )
    expected_brier = (1 - probability_after_tie) ** 2

    assert float(evaluation["brier_score"]) == pytest.approx(expected_brier)
    assert int(evaluation["matches_evaluated"]) == 1
    assert int(evaluation["matches_skipped"]) == 1


def test_benchmark_rejects_period_with_no_decisive_matches(tmp_path):
    training_data = tmp_path / "training.csv"
    verification_data = tmp_path / "verification.csv"
    output_path = tmp_path / "evaluation.csv"

    write_matches(
        training_data,
        [match("001", "2026-01-01", "Alpha", "Beta", "Alpha")],
    )
    write_matches(
        verification_data,
        [
            match("002", "2026-02-01", "Alpha", "Beta", "tie"),
            match("003", "2026-03-01", "Alpha", "Beta", "no result"),
        ],
    )

    result = benchmark(training_data, verification_data, output_path)

    assert result is False
    assert not output_path.exists()


def test_benchmark_is_deterministic(tmp_path):
    training_data = tmp_path / "training.csv"
    verification_data = tmp_path / "verification.csv"
    first_output = tmp_path / "first_evaluation.csv"
    second_output = tmp_path / "second_evaluation.csv"

    write_matches(
        training_data,
        [match("001", "2026-01-01", "Alpha", "Beta", "Alpha")],
    )
    write_matches(
        verification_data,
        [
            match("002", "2026-02-01", "Alpha", "Beta", "Beta"),
            match("003", "2026-03-01", "Alpha", "Beta", "Alpha"),
        ],
    )

    first_result = benchmark(training_data, verification_data, first_output)
    second_result = benchmark(training_data, verification_data, second_output)

    assert first_result is True
    assert second_result is True
    assert first_output.read_text(encoding="utf-8") == second_output.read_text(
        encoding="utf-8"
    )
