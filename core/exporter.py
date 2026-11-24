"""Export results: CSV (performance metrics) and JSON (detailed results + replay log)."""

import csv
import io
import json
import os
import re
from datetime import datetime

from core.maze import Maze
from core.metrics import build_metrics

FORMAT_VERSION = 1

CSV_COLUMNS = [
    "algorithm", "path_found", "path_length", "runtime_ms", "expanded_nodes",
    "total_walkable_cells", "explored_density_percent",
    "grid_rows", "grid_cols", "start_row", "start_col", "goal_row", "goal_col", "error",
]

NOTES = {
    "cells": "Positions are [row, col]. Row 0 is the top row, column 0 is the left column.",
    "moves": "Four directions only (up, down, left, right). Every move costs 1.",
    "expanded_nodes": "Nodes taken out of the priority queue and processed (stale duplicates not counted).",
    "explored_density_percent": "expanded_nodes / walkable_cells * 100.",
    "steps": ("Replay log. Each step = one node taken from the queue ('expanded') plus the "
              "neighbours it added to the waiting list ('pushed'). Replay them in order to "
              "reproduce the animation."),
}


def _cell(pos):
    return [int(pos[0]), int(pos[1])]          # plain ints, so json.dumps never fails


# ---------------------------------------------------------------- CSV
def to_csv(maze, results):
    """One row per algorithm run. Numbers only, so it opens cleanly in Excel or pandas."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for res in results:
        m = build_metrics(res, maze)
        writer.writerow({
            "algorithm": m["algorithm"],
            "path_found": m["path_found"],
            "path_length": "" if m["path_length"] is None else m["path_length"],
            "runtime_ms": round(m["runtime_ms"], 4),
            "expanded_nodes": m["expanded_nodes"],
            "total_walkable_cells": m["total_walkable_cells"],
            "explored_density_percent": round(m["explored_density_percent"], 4),
            "grid_rows": maze.rows,
            "grid_cols": maze.cols,
            "start_row": maze.start[0],
            "start_col": maze.start[1],
            "goal_row": maze.goal[0],
            "goal_col": maze.goal[1],
            "error": m["error"],
        })
    return buffer.getvalue()


# ---------------------------------------------------------------- JSON
def maze_to_export(maze):
    """The maze as readable text: one string of 0/1 characters per row."""
    return {
        "rows": maze.rows,
        "cols": maze.cols,
        "start": _cell(maze.start),
        "goal": _cell(maze.goal),
        "wall_count": maze.rows * maze.cols - maze.total_walkable(),
        "walkable_cells": maze.total_walkable(),
        "grid_legend": {"0": "empty", "1": "wall"},
        "grid": ["".join(str(int(v)) for v in row) for row in maze.grid],
    }


def maze_from_export(data):
    """Rebuild a Maze from the 'maze' part of an exported JSON file."""
    maze = Maze(data["rows"], data["cols"], tuple(data["start"]), tuple(data["goal"]))
    for r, line in enumerate(data["grid"]):
        for c, char in enumerate(line):
            maze.grid[r, c] = int(char)
    return maze


def run_to_export(maze, res, include_steps=True):
    m = build_metrics(res, maze)
    run = {
        "algorithm": res.algorithm,
        "path_found": res.found,
        "path_length": m["path_length"],
        "runtime_ms": round(m["runtime_ms"], 4),
        "expanded_nodes": m["expanded_nodes"],
        "total_walkable_cells": m["total_walkable_cells"],
        "explored_density_percent": round(m["explored_density_percent"], 4),
        "error": res.error,
        "path": [_cell(p) for p in res.path],
    }
    if include_steps:
        run["steps"] = [
            {"step": i, "expanded": _cell(node), "pushed": [_cell(p) for p in pushed]}
            for i, (node, pushed) in enumerate(res.steps, start=1)
        ]
    return run


def build_export(maze, results, include_steps=True, exported_at=None):
    """Everything in one dictionary (the JSON file is just this, written as text)."""
    if exported_at is None:
        exported_at = datetime.now().isoformat(timespec="seconds")
    return {
        "format_version": FORMAT_VERSION,
        "exported_at": exported_at,
        "notes": NOTES,
        "maze": maze_to_export(maze),
        "runs": [run_to_export(maze, res, include_steps) for res in results],
    }


def _compact_number_lists(text):
    """Pretty-printing tweak: keep [row, col] pairs and lists of pairs on ONE line.
    Only whitespace changes, so the JSON means exactly the same thing."""
    def one_line_numbers(match):
        return "[" + re.sub(r"\s*,\s*", ", ", match.group(1)) + "]"

    def one_line_pairs(match):
        return "[" + re.sub(r"\]\s*,\s*\[", "], [", match.group(1)) + "]"

    text = re.sub(r"\[\s*(-?\d+(?:\s*,\s*-?\d+)*)\s*\]", one_line_numbers, text)
    text = re.sub(r"\[\s*(\[[-\d, ]*\](?:\s*,\s*\[[-\d, ]*\])*)\s*\]", one_line_pairs, text)
    return text


def to_json(data):
    return _compact_number_lists(json.dumps(data, indent=2))


# ---------------------------------------------------------------- files on disk
def save_exports(maze, results, folder="exports", name=None, include_steps=True):
    """Write <name>.csv and <name>.json into `folder` (created if missing).
    Returns {"csv": path, "json": path}."""
    os.makedirs(folder, exist_ok=True)
    base = name or "pathfinding_results_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = {"csv": os.path.join(folder, base + ".csv"),
             "json": os.path.join(folder, base + ".json")}
    with open(paths["csv"], "w", encoding="utf-8", newline="") as f:
        f.write(to_csv(maze, results))
    with open(paths["json"], "w", encoding="utf-8") as f:
        f.write(to_json(build_export(maze, results, include_steps)))
    return paths