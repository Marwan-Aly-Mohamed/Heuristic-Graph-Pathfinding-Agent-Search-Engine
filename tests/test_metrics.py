import pytest

from core.maze import Maze
from core.metrics import build_metrics, compare_summary, display_rows, explored_density
from core.pathfinding import ALGORITHMS, compare_algorithms, format_table, run_search


def test_density_formula():
    assert explored_density(50, 200) == 25.0
    assert explored_density(0, 100) == 0.0
    assert explored_density(10, 0) == 0.0        # no division by zero


def test_unknown_algorithm_name():
    with pytest.raises(ValueError):
        run_search(Maze(5, 5), "BFS")


@pytest.mark.parametrize("name", list(ALGORITHMS))
def test_runtime_is_measured(name):
    r = run_search(Maze(30, 30), name)
    assert r.runtime_seconds > 0
    assert r.runtime_seconds < 5                 # sanity: a 30x30 grid is fast


@pytest.mark.parametrize("name", list(ALGORITHMS))
def test_metrics_values_are_consistent(name):
    m = Maze.random(20, 20, 0.2, seed=15)
    r = run_search(m, name)
    row = build_metrics(r, m)
    assert row["algorithm"] == name
    assert row["expanded_nodes"] == r.expanded_nodes
    assert row["total_walkable_cells"] == m.total_walkable()
    expected = r.expanded_nodes / m.total_walkable() * 100
    assert row["explored_density_percent"] == pytest.approx(expected)
    if r.found:
        assert row["path_length"] == len(r.path) - 1


@pytest.mark.parametrize("name", list(ALGORITHMS))
def test_not_found_has_no_path_length(name):
    m = Maze(5, 5)
    for r_ in range(5):
        m.add_wall((r_, 2))
    row = build_metrics(run_search(m, name), m)
    assert row["path_found"] is False
    assert row["path_length"] is None
    assert row["error"]


@pytest.mark.parametrize("name", list(ALGORITHMS))
def test_invalid_start_is_reported_not_crashed(name):
    m = Maze(5, 5)
    m.start = (9, 9)
    row = build_metrics(run_search(m, name), m)
    assert row["path_found"] is False and "outside" in row["error"]
    assert row["expanded_nodes"] == 0 and row["explored_density_percent"] == 0.0


@pytest.mark.parametrize("name", list(ALGORITHMS))
def test_search_does_not_change_the_maze(name):
    m = Maze.random(15, 15, 0.3, seed=2)
    before = m.grid.copy()
    run_search(m, name)
    assert (m.grid == before).all()


def test_density_always_between_0_and_100():
    for seed in range(30):
        m = Maze.random(20, 20, 0.35, seed=seed)
        for name in ALGORITHMS:
            d = build_metrics(run_search(m, name), m)["explored_density_percent"]
            assert 0 <= d <= 100


def test_compare_uses_same_maze_and_gives_same_cost():
    m = Maze.random(30, 30, 0.2, seed=3)
    results, rows = compare_algorithms(m, repeats=3)
    assert [r["algorithm"] for r in rows] == ["A*", "Dijkstra"]
    assert rows[0]["total_walkable_cells"] == rows[1]["total_walkable_cells"]
    if rows[0]["path_found"]:
        assert rows[0]["path_length"] == rows[1]["path_length"]
        assert rows[0]["expanded_nodes"] <= rows[1]["expanded_nodes"]


def test_format_table_runs():
    m = Maze.random(10, 10, 0.2, seed=3)
    text = format_table(compare_algorithms(m)[1])
    assert "A*" in text and "Dijkstra" in text


def make_row(name, found=True, length=10, ms=1.0, expanded=50, walkable=100):
    return {
        "algorithm": name, "path_found": found, "path_length": length if found else None,
        "runtime_ms": ms, "expanded_nodes": expanded, "total_walkable_cells": walkable,
        "explored_density_percent": expanded / walkable * 100, "error": "",
    }


def test_display_rows_use_friendly_names_and_rounding():
    row = make_row("A*", ms=1.23456, expanded=33, walkable=99)
    shown = display_rows([row])[0]
    assert shown["Algorithm"] == "A*"
    assert shown["Path found"] == "Yes"
    assert shown["Execution time (ms)"] == 1.235
    assert shown["Explored density (%)"] == 33.33
    assert shown["Expanded nodes"] == 33


def test_display_rows_for_a_failed_search():
    shown = display_rows([make_row("Dijkstra", found=False)])[0]
    assert shown["Path found"] == "No" and shown["Path length (moves)"] is None


def test_summary_astar_fewer_nodes_and_faster():
    text = compare_summary([make_row("A*", expanded=25, ms=1.0), make_row("Dijkstra", expanded=100, ms=4.0)])
    assert "shortest path of 10 moves" in text
    assert "25 nodes versus 100" in text and "75% fewer" in text
    assert "4.0x faster" in text


def test_summary_astar_slower_explains_why():
    text = compare_summary([make_row("A*", ms=3.0), make_row("Dijkstra", ms=1.0)])
    assert "3.0x slower" in text and "heuristic" in text


def test_summary_when_nothing_is_found():
    a = make_row("A*", found=False, expanded=200)
    d = make_row("Dijkstra", found=False, expanded=200)
    text = compare_summary([a, d])
    assert "Neither" in text and "200" in text


def test_summary_equal_nodes_and_missing_algorithm():
    assert "Both expanded 40 nodes" in compare_summary(
        [make_row("A*", expanded=40), make_row("Dijkstra", expanded=40)])
    assert compare_summary([make_row("A*")]) == ""


def test_summary_on_real_results():
    m = Maze.random(30, 30, 0.2, seed=3)
    rows = compare_algorithms(m, repeats=1)[1]
    text = compare_summary(rows)
    if rows[0]["path_found"]:
        assert "moves" in text
        assert "fewer" in text or "Both expanded" in text