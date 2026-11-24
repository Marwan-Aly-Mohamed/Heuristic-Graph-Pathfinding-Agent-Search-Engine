import csv
import io
import json

import numpy as np

from core.exporter import (CSV_COLUMNS, build_export, maze_from_export, save_exports,
                           to_csv, to_json)
from core.maze import Maze
from core.pathfinding import compare_algorithms, run_search


def solved_maze():
    maze, _ = Maze.random_solvable(20, 30, 0.25, seed=2)
    return maze


def read_csv(text):
    return list(csv.DictReader(io.StringIO(text)))


# ---------------------------------------------------------------- CSV
def test_csv_has_the_expected_columns_and_one_row_per_run():
    m = solved_maze()
    results, _ = compare_algorithms(m, repeats=1)
    text = to_csv(m, results)
    assert text.splitlines()[0] == ",".join(CSV_COLUMNS)
    rows = read_csv(text)
    assert [r["algorithm"] for r in rows] == ["A*", "Dijkstra"]


def test_csv_values_match_the_results():
    m = solved_maze()
    results, _ = compare_algorithms(m, repeats=1)
    rows = read_csv(to_csv(m, results))
    for row, res in zip(rows, results):
        assert row["path_found"] == "True"
        assert int(row["path_length"]) == res.path_length
        assert int(row["expanded_nodes"]) == res.expanded_nodes
        assert int(row["total_walkable_cells"]) == m.total_walkable()
        assert float(row["runtime_ms"]) > 0
        expected_density = res.expanded_nodes / m.total_walkable() * 100
        assert abs(float(row["explored_density_percent"]) - expected_density) < 0.001
        assert (int(row["grid_rows"]), int(row["grid_cols"])) == (m.rows, m.cols)
        assert (int(row["start_row"]), int(row["start_col"])) == m.start
        assert (int(row["goal_row"]), int(row["goal_col"])) == m.goal


def test_csv_for_a_failed_search_has_empty_path_length_and_an_error():
    m = Maze(6, 6)
    for r in range(6):
        m.add_wall((r, 3))
    rows = read_csv(to_csv(m, [run_search(m, "A*")]))
    assert rows[0]["path_found"] == "False"
    assert rows[0]["path_length"] == ""
    assert rows[0]["error"]


# ---------------------------------------------------------------- JSON
def test_json_text_is_valid_and_equals_the_dictionary():
    m = solved_maze()
    results, _ = compare_algorithms(m, repeats=1)
    data = build_export(m, results, exported_at="2026-01-01T00:00:00")
    assert json.loads(to_json(data)) == data          # pretty-printing changed nothing


def test_json_contains_everything_the_brief_asks_for():
    m = solved_maze()
    results, _ = compare_algorithms(m, repeats=1)
    data = build_export(m, results)
    assert data["maze"]["rows"] == m.rows and data["maze"]["cols"] == m.cols
    assert data["maze"]["start"] == list(m.start) and data["maze"]["goal"] == list(m.goal)
    assert len(data["maze"]["grid"]) == m.rows
    assert all(len(line) == m.cols for line in data["maze"]["grid"])
    for run, res in zip(data["runs"], results):
        assert run["algorithm"] == res.algorithm
        assert run["path_found"] is True
        assert run["path"] == [list(p) for p in res.path]
        assert run["path_length"] == res.path_length
        assert run["runtime_ms"] > 0
        assert run["expanded_nodes"] == res.expanded_nodes
        assert "explored_density_percent" in run


def test_json_steps_log_matches_the_search():
    m = solved_maze()
    res = run_search(m, "A*")
    run = build_export(m, [res])["runs"][0]
    steps = run["steps"]
    assert len(steps) == res.expanded_nodes
    assert steps[0]["expanded"] == list(m.start) and steps[0]["step"] == 1
    assert steps[-1]["expanded"] == list(m.goal)
    assert [s["step"] for s in steps] == list(range(1, len(steps) + 1))


def test_json_without_steps_is_smaller():
    m = solved_maze()
    results, _ = compare_algorithms(m, repeats=1)
    with_steps = to_json(build_export(m, results, include_steps=True))
    without = to_json(build_export(m, results, include_steps=False))
    assert "steps" not in json.loads(without)["runs"][0]
    assert len(without) < len(with_steps) / 2


def test_json_failed_search():
    m = Maze(6, 6)
    for r in range(6):
        m.add_wall((r, 3))
    run = build_export(m, [run_search(m, "Dijkstra")])["runs"][0]
    assert run["path_found"] is False and run["path"] == []
    assert run["path_length"] is None and run["error"]


def test_json_invalid_start_does_not_crash():
    m = Maze(5, 5)
    m.start = (9, 9)
    data = build_export(m, [run_search(m, "A*")])
    assert data["runs"][0]["path_found"] is False
    json.loads(to_json(data))


def test_numpy_integers_never_break_the_export():
    m = Maze(5, 5, start=(np.int64(0), np.int64(0)), goal=(np.int64(4), np.int64(4)))
    res = run_search(m, "A*")
    json.loads(to_json(build_export(m, [res])))


def test_pretty_printing_keeps_the_file_short():
    m = solved_maze()
    res = run_search(m, "Dijkstra")
    text = to_json(build_export(m, [res]))
    assert text.count("\n") < len(res.steps) * 8 + 200


def test_maze_round_trip_through_json():
    m = Maze.random(12, 17, 0.3, seed=5)
    if m.is_walkable((3, 3)) and (3, 3) != m.start:
        m.set_goal((3, 3))                       # a non-default goal, so we test it too
    data = json.loads(to_json(build_export(m, [run_search(m, "A*")])))
    copy = maze_from_export(data["maze"])
    assert (copy.grid == m.grid).all()
    assert copy.start == m.start and copy.goal == m.goal
    assert copy.signature() == m.signature()


def test_exported_search_can_be_replayed_to_the_same_explored_cells():
    m = solved_maze()
    res = run_search(m, "Dijkstra")
    data = json.loads(to_json(build_export(m, [res])))
    replayed = {tuple(s["expanded"]) for s in data["runs"][0]["steps"]}
    assert replayed == {node for node, _ in res.steps}


# ---------------------------------------------------------------- files
def test_save_exports_creates_the_folder_and_both_files(tmp_path):
    m = solved_maze()
    results, _ = compare_algorithms(m, repeats=1)
    folder = tmp_path / "new_folder" / "exports"
    paths = save_exports(m, results, folder=str(folder), name="run1")
    assert paths["csv"].endswith("run1.csv") and paths["json"].endswith("run1.json")
    with open(paths["csv"], encoding="utf-8") as f:
        assert len(read_csv(f.read())) == 2
    with open(paths["json"], encoding="utf-8") as f:
        assert len(json.load(f)["runs"]) == 2


def test_save_exports_default_name_has_a_timestamp(tmp_path):
    m = solved_maze()
    paths = save_exports(m, [run_search(m, "A*")], folder=str(tmp_path))
    assert "pathfinding_results_" in paths["csv"]