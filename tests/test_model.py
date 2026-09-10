import pytest

from cricket_elo.model import (
    adjust_elo,
    expected_score,
    score_for_team,
    select_k_factor,
)


def test_equal_ratings_have_equal_probability():
    probability = expected_score(1500, 1500)

    assert probability == pytest.approx(0.5)


def test_probabilities_are_complementary():
    probability_a = expected_score(1600, 1500)
    probability_b = expected_score(1500, 1600)

    assert probability_a + probability_b == pytest.approx(1.0)


def test_k_factor_changes_after_provisional_period():
    assert select_k_factor(6) == 100
    assert select_k_factor(7) == 64


def test_equal_k_factors_conserve_rating_points():
    new_a, new_b = adjust_elo(
        1500,
        1500,
        100,
        100,
        1,
    )

    assert new_a == pytest.approx(1550)
    assert new_b == pytest.approx(1450)

def test_provisional_team_moves_more():
    new_a, new_b = adjust_elo(
        1500,
        1500,
        100,
        64,
        1,
    )

    movement_a = abs(new_a - 1500)
    movement_b = abs(new_b - 1500)

    assert movement_a > movement_b

def test_result_is_converted_to_correct_score():
    assert score_for_team("England", "England") == 1
    assert score_for_team("India", "England") == 0
    assert score_for_team("tie", "England") == pytest.approx(0.5)