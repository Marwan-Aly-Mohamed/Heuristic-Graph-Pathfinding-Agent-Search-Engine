import pytest

from algorithms.astar import astar
from algorithms.dijkstra import dijkstra
from core.maze import Maze
from tests.helpers import assert_valid_path, bfs_shortest_moves


def test_open_grid_straight_path():
    m = Maze(5, 5)
    r = dijkstra(m)
    assert r.found and r.path_length == 8
    assert_valid_path(m, r)


def test_detour_around_wall():
    m = Maze(3, 3, start=(1, 0), goal=(1, 2))
    m.add_wall((1, 1))
    r = dijkstra(m)
    assert r.found and r.path_length == 4
    assert_valid_path(m, r)


def test_start_equals_goal():
    m = Maze(4, 4, start=(2, 2), goal=(2, 2))
    r = dijkstra(m)
    assert r.found and r.path_length == 0 and r.path == [(2, 2)]
    assert r.expanded_nodes == 1


def test_unreachable_goal():
    m = Maze(5, 5)
    for r_ in range(5):
        m.add_wall((r_, 2))
    r = dijkstra(m)
    assert not r.found and r.path == [] and r.error


def test_invalid_positions_give_error_not_crash():
    m = Maze(5, 5)
    m.start = (9, 9)
    assert dijkstra(m).error and not dijkstra(m).found
    m = Maze(5, 5)
    m.grid[m.goal] = 1
    assert dijkstra(m).error and not dijkstra(m).found


@pytest.mark.parametrize("size", [(5, 5), (10, 10), (30, 30), (50, 50), (20, 60)])
@pytest.mark.parametrize("density", [0.0, 0.1, 0.3, 0.45])
def test_matches_bfs_on_random_mazes(size, density):
    for seed in range(15):
        m = Maze.random(size[0], size[1], density, seed=seed)
        expected = bfs_shortest_moves(m)
        r = dijkstra(m)
        if expected is None:
            assert not r.found
        else:
            assert r.found and r.path_length == expected
            assert_valid_path(m, r)


def test_expanded_count_matches_steps_log():
    m = Maze.random(15, 15, 0.2, seed=15)
    r = dijkstra(m)
    assert r.expanded_nodes == len(r.steps)


# ---------- A* vs Dijkstra: same maze, same rules ----------
@pytest.mark.parametrize("density", [0.0, 0.15, 0.3, 0.45, 0.7])
def test_same_cost_and_astar_never_expands_more(density):
    for seed in range(25):
        m = Maze.random(25, 25, density, seed=seed)
        a, d = astar(m), dijkstra(m)
        assert a.found == d.found
        if a.found:
            assert a.path_length == d.path_length        # same optimal cost
            assert a.expanded_nodes <= d.expanded_nodes  # A* is never worse
        else:
            assert a.expanded_nodes == d.expanded_nodes  # both exhaust the reachable area