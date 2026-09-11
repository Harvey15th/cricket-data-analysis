import csv
import os
import subprocess
import sys

from matplotlib.image import imread


PREDICTION_FIELDS = [
    "match_id",
    "date",
    "team1",
    "team2",
    "result",
    "elo_team1_before",
    "elo_team2_before",
    "p_team1",
    "actual_score",
    "status",
    "elo_brier",
    "baseline_brier",
]


def write_predictions(path):
    # After Alpha wins the first match, ratings are 1550 and 1450.
    # The no-result changes nothing; the tie then moves ratings closer.
    rows = [
        (
            "001", "2026-02-01", "Alpha", "Beta", "Alpha",
            1500.0, 1500.0, 0.5, 1.0, "evaluated", 0.25, 0.25,
        ),
        (
            "002", "2026-02-02", "Alpha", "Beta", "no result",
            1550.0, 1450.0, 0.6400649998028851, "", "no_result", "", "",
        ),
        (
            "003", "2026-02-03", "Alpha", "Beta", "tie",
            1550.0, 1450.0, 0.6400649998028851, 0.5, "tie", "", "",
        ),
        (
            "004", "2026-02-04", "Alpha", "Beta", "Alpha",
            1535.9935000197115, 1464.0064999802885, 0.6021401655765967,
            1.0, "evaluated", 0.15829244784741792, 0.25,
        ),
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PREDICTION_FIELDS)
        writer.writerows(rows)


def test_plot_command_saves_readable_png_from_mixed_results(tmp_path):
    # Spaces in paths also check that the command receives complete paths.
    work_directory = tmp_path / "plot test"
    work_directory.mkdir()
    input_path = work_directory / "prediction log.csv"
    output_path = work_directory / "brier chart.png"
    write_predictions(input_path)

    # Agg saves image files without opening an interactive plot window.
    # Give Matplotlib its own temporary configuration/cache directory.
    config_directory = tmp_path / "matplotlib config"
    config_directory.mkdir()
    environment = os.environ.copy()
    environment["MPLBACKEND"] = "Agg"
    environment["MPLCONFIGDIR"] = str(config_directory)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cricket_elo",
            "plot",
            "--eval-log",
            str(input_path),
            "--output",
            str(output_path),
        ],
        cwd=work_directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, (
        f"Plot command exited with {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert output_path.is_file(), "Plot command did not create the requested file."
    assert output_path.stat().st_size > 0, "The output file is empty."

    with output_path.open("rb") as file:
        assert file.read(8) == b"\x89PNG\r\n\x1a\n", "Output is not a PNG file."

    # Decode the image to catch corrupt files. Avoid exact pixel snapshots:
    # fonts and rendering can differ between Windows and GitHub's Linux runner.
    pixels = imread(output_path)
    assert pixels.ndim in (2, 3), "Expected a grayscale or colour image."
    assert pixels.shape[0] > 1 and pixels.shape[1] > 1
    assert (pixels != pixels[0, 0]).any(), "The image is a single uniform colour."