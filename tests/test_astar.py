import pytest

from algorithms.astar import astar, manhattan
from core.maze import Maze
from tests.helpers import assert_valid_path, bfs_shortest_moves

def test_manhattan():
    assert manhattan((0, 0), (3, 4)) == 7
    assert manhattan((2, 2), (2, 2)) == 0


def test_open_grid_straight_path():
    m = Maze(5, 5)
    r = astar(m)
    assert r.found
    assert r.path_length == 8            # 4 down + 4 right
    assert_valid_path(m, r)


def test_detour_around_wall():
    m = Maze(3, 3, start=(1, 0), goal=(1, 2))
    m.add_wall((1, 1))
    r = astar(m)
    assert r.found and r.path_length == 4   # must go around the wall
    assert_valid_path(m, r)


def test_start_equals_goal():
    m = Maze(4, 4, start=(2, 2), goal=(2, 2))
    r = astar(m)
    assert r.found and r.path_length == 0 and r.path == [(2, 2)]
    assert r.expanded_nodes == 1


def test_unreachable_goal():
    m = Maze(5, 5)
    for r_ in range(5):
        m.add_wall((r_, 2))              # full wall column
    r = astar(m)
    assert not r.found
    assert r.path == [] and r.error


def test_goal_walled_in():
    m = Maze(5, 5)
    for pos in [(3, 4), (4, 3)]:         # block both neighbors of the goal
        m.add_wall(pos)
    assert not astar(m).found


def test_invalid_positions_give_error_not_crash():
    m = Maze(5, 5)
    m.start = (9, 9)
    assert astar(m).error and not astar(m).found
    m = Maze(5, 5)
    m.grid[m.start] = 1
    assert astar(m).error and not astar(m).found


@pytest.mark.parametrize("size", [(5, 5), (10, 10), (30, 30), (50, 50), (20, 60)])
@pytest.mark.parametrize("density", [0.0, 0.1, 0.3, 0.45])
def test_matches_bfs_on_random_mazes(size, density):
    """Many seeds, small->medium sizes, low->high density."""
    for seed in range(15):
        m = Maze.random(size[0], size[1], density, seed=seed)
        expected = bfs_shortest_moves(m)
        r = astar(m)
        if expected is None:
            assert not r.found
        else:
            assert r.found
            assert r.path_length == expected     # optimal!
            assert_valid_path(m, r)


def test_very_high_density_mostly_unreachable():
    found = 0
    for seed in range(30):
        m = Maze.random(20, 20, 0.8, seed=seed)
        r = astar(m)
        assert r.found == (bfs_shortest_moves(m) is not None)
        found += r.found
    assert found < 30


def test_expanded_count_matches_steps_log():
    m = Maze.random(15, 15, 0.2, seed=15)
    r = astar(m)
    assert r.expanded_nodes == len(r.steps)