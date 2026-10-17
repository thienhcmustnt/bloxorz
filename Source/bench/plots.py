"""Report-ready grouped figures, with missing measurements explicitly left blank."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

METRICS = {
    "search_time_s": "Search time (s)",
    "peak_memory_kb": "Peak traced memory (KB)",
    "expanded_nodes": "Expanded nodes",
    "solution_length": "Solution length (actions)",
}


def plot_results(csv_path: Path, out: Path) -> list[Path]:
    """Draw four figures, each with four group panels and per-level bars.

    No averaging across differently solved subsets; a missing/failed run has no
    bar. The Markdown table retains failure reasons and all measured costs.
    """
    with csv_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    out.mkdir(parents=True, exist_ok=True)
    solved = [r for r in rows if r["found"].lower() == "true"]
    labels = sorted({r["algo"] + (":" + r["heuristic"] if r["heuristic"] else "") for r in rows})
    paths: list[Path] = []
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    for metric, title in METRICS.items():
        figure, axes = plt.subplots(2, 2, figsize=(14, 8), layout="constrained")
        for group, ax in enumerate(axes.flat, 1):
            group_rows = [r for r in solved if int(r["group"]) == group]
            ids = sorted({int(r["level_id"]) for r in rows if int(r["group"]) == group})
            width = 0.8 / max(1, len(labels))
            for index, label in enumerate(labels):
                data = {
                    int(r["level_id"]): float(r[metric])
                    for r in group_rows
                    if r["algo"] + (":" + r["heuristic"] if r["heuristic"] else "") == label
                }
                xs = [
                    i - 0.4 + (index + 0.5) * width for i, level in enumerate(ids) if level in data
                ]
                ys = [data[level] for level in ids if level in data]
                ax.bar(xs, ys, width, label=label)
            values = [float(r[metric]) for r in group_rows if float(r[metric]) > 0]
            if values and max(values) / min(values) >= 100:
                ax.set_yscale("log")
            ax.set_title(f"Group {group}")
            ax.set_ylabel(title)
            ax.set_xticks(range(len(ids)), [f"L{i:02d}" for i in ids])
            ax.grid(axis="y", alpha=0.18)
            ax.set_axisbelow(True)
            if not group_rows:
                ax.text(
                    0.5,
                    0.5,
                    "No successful measurements",
                    transform=ax.transAxes,
                    ha="center",
                    color="#697888",
                )
        if labels:
            handles, legend_labels = axes.flat[0].get_legend_handles_labels()
            figure.legend(
                handles,
                legend_labels,
                loc="outside lower center",
                ncol=min(6, len(labels)),
                frameon=False,
            )
        figure.suptitle(title + " · Bloxorz", fontsize=16)
        target = out / (metric + ".png")
        figure.savefig(target, dpi=240)
        plt.close(figure)
        paths.append(target)
    lines = [
        "# Benchmark results",
        "",
        "Separate time/memory runs; median of complete repetitions. Missing bars are not zero.",
        "",
        "| Algorithm | Heuristic | Level | Group | Found | Length | Cost | Expanded | Time (s) | Peak (KB) | Reason |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                str(row.get(k, "")).replace("|", "/").replace("\n", " ")
                for k in [
                    "algo",
                    "heuristic",
                    "level_id",
                    "group",
                    "found",
                    "solution_length",
                    "cost",
                    "expanded_nodes",
                    "search_time_s",
                    "peak_memory_kb",
                    "reason",
                ]
            )
            + " |"
        )
    if not rows:
        lines += ["", "No implemented solver was available. This is not an experimental result."]
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return paths


def main() -> None:
    """Regenerate figures from an existing results.csv."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    plot_results(args.csv, args.out or args.csv.parent)


if __name__ == "__main__":
    main()
