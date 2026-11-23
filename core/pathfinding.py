"""The ONE entry point used by tests, the UI and the exports.
It runs an algorithm on a maze, times it, and returns the same format for both."""

import statistics
import time

from algorithms.astar import astar
from algorithms.dijkstra import dijkstra
from core.metrics import build_metrics

ALGORITHMS = {"A*": astar, "Dijkstra": dijkstra}


def run_search(maze, algorithm_name, repeats=1):
    """Run one algorithm and measure ONLY the search itself.

    repeats > 1 runs it several times and keeps the median time,
    which smooths out random hiccups from the operating system."""
    if algorithm_name not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm '{algorithm_name}'. Choose from {list(ALGORITHMS)}.")
    algorithm = ALGORITHMS[algorithm_name]

    times = []
    for _ in range(max(1, repeats)):
        t0 = time.perf_counter()
        result = algorithm(maze)
        times.append(time.perf_counter() - t0)

    result.runtime_seconds = statistics.median(times)
    return result


def compare_algorithms(maze, repeats=5):
    """Run A* and Dijkstra on the SAME maze. Returns (results, metrics_rows)."""
    results = [run_search(maze, name, repeats) for name in ALGORITHMS]
    rows = [build_metrics(r, maze) for r in results]
    return results, rows


def format_table(rows):
    """Plain-text table for the terminal (the UI will use a nicer one)."""
    headers = ["algorithm", "path_found", "path_length", "runtime_ms",
               "expanded_nodes", "explored_density_percent"]
    def cell(key, value):
        if isinstance(value, float):
            return f"{value:.3f}" if key == "runtime_ms" else f"{value:.2f}"
        return "-" if value is None else str(value)
    table = [[cell(h, row[h]) for h in headers] for row in rows]
    widths = [max(len(h), *(len(r[i]) for r in table)) for i, h in enumerate(headers)]
    lines = ["  ".join(h.ljust(w) for h, w in zip(headers, widths))]
    lines.append("  ".join("-" * w for w in widths))
    for r in table:
        lines.append("  ".join(v.ljust(w) for v, w in zip(r, widths)))
    return "\n".join(lines)