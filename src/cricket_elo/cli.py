import argparse
from .benchmark import benchmark
from .predict import predict
from .prepare import prepare
from .train import train

def main_cli():
    parser = build_parser()
    args = parser.parse_args()
    result = args.func(args)

    if result:
        return 0
    else:
        return 1

def run_benchmark(args):
    return benchmark(args.training_data, args.verification_data)

def run_predict(args):
    return predict(args.ratings, args.team_a, args.team_b)

def run_prepare(args):
    return prepare(args.input, args.output)

def run_train(args):
    return train(args.input_data, args.output)


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
    prepare_parser.set_defaults(
        func = run_prepare
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
    train_parser.set_defaults(
        func = run_train
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
    predict_parser.set_defaults(
        func = run_predict
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
    benchmark_parser.set_defaults(
        func = run_benchmark
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