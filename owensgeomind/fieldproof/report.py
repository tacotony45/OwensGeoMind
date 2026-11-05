
"""CSV reporting for FieldProof Lite."""

import csv
from pathlib import Path


def export_issues_csv(issues, output_path):
    """Export GIS validation issues without overwriting files."""

    columns = ["feature_id", "rule", "message"]

    path = Path(output_path).expanduser()

    if path.suffix.lower() != ".csv":
        raise ValueError("Report filename must end in .csv")

    if path.exists():
        raise FileExistsError(
            f"Report already exists: {path}"
        )

    with path.open(
        "x",
        newline="",
        encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            extrasaction="ignore"
        )

        writer.writeheader()

        for issue in issues:
            writer.writerow(issue)

    return str(path)
