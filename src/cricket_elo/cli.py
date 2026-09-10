import argparse


def build_parser() -> argparse.ArgumentParser:
    """Create and return the Cricket Elo argument parser."""

    parser = argparse.ArgumentParser(
        prog="cricket-elo",
        description="Analyse historical T20I matches using Elo ratings.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    prepare_parser = subparsers.add_parser(
        "prepare",
        help="Convert Cricsheet JSON files into processed match data.",
    )
    prepare_parser.add_argument(
        "--input",
        required=True,
        help="Directory containing Cricsheet JSON files.",
    )
    prepare_parser.add_argument(
        "--output",
        required=True,
        help="Path for the processed CSV file.",
    )

    train_parser = subparsers.add_parser(
        "train",
        help="Calculate Elo ratings from processed match data.",
    )
    train_parser.add_argument(
        "--input-data",
        required=True,
        help="Path to the processed match CSV file.",
    )
    train_parser.add_argument(
        "--output",
        required=True,
        help="Path for the generated team ratings.",
    )

    predict_parser = subparsers.add_parser(
        "predict",
        help="Estimate the win probability between two teams.",
    )
    predict_parser.add_argument(
        "--ratings",
        required=True,
        help="Path to a generated team-ratings CSV file.",
    )
    predict_parser.add_argument(
        "--team-a",
        required=True,
        help="Name of the first team.",
    )
    predict_parser.add_argument(
        "--team-b",
        required=True,
        help="Name of the second team.",
    )

    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="Run the experimental Elo benchmark.",
    )
    benchmark_parser.add_argument(
        "--training-data",
        required=True,
        help="Path to the older training-match data.",
    )
    benchmark_parser.add_argument(
        "--verification-data",
        required=True,
        help="Path to the later verification-match data.",
    )

    return parser