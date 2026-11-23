import pytest

from core.maze import Maze


def test_default_start_and_goal():
    m = Maze(5, 7)
    assert m.start == (0, 0)
    assert m.goal == (4, 6)
    assert m.total_walkable() == 35


def test_invalid_size():
    with pytest.raises(ValueError):
        Maze(0, 5)
    with pytest.raises(ValueError):
        Maze(1000, 1000)


def test_add_and_remove_wall():
    m = Maze(5, 5)
    m.add_wall((2, 2))
    assert not m.is_walkable((2, 2))
    assert m.total_walkable() == 24
    m.remove_wall((2, 2))
    assert m.is_walkable((2, 2))


def test_cannot_wall_start_or_goal():
    m = Maze(5, 5)
    with pytest.raises(ValueError):
        m.add_wall(m.start)
    with pytest.raises(ValueError):
        m.add_wall(m.goal)


def test_set_start_goal_rules():
    m = Maze(5, 5)
    m.add_wall((1, 1))
    with pytest.raises(ValueError):
        m.set_start((1, 1))      # wall
    with pytest.raises(ValueError):
        m.set_goal((9, 9))       # outside
    m.set_start((2, 2))
    assert m.start == (2, 2)


def test_neighbors_corner_and_center():
    m = Maze(5, 5)
    assert sorted(m.neighbors((0, 0))) == [(0, 1), (1, 0)]
    assert len(m.neighbors((2, 2))) == 4
    m.add_wall((2, 3))
    assert (2, 3) not in m.neighbors((2, 2))


def test_validate_catches_bad_positions():
    m = Maze(5, 5)
    m.start = (10, 10)
    assert m.validate() is not None
    m.start = (0, 0)
    m.grid[m.goal] = 1
    assert m.validate() is not None


def test_random_maze_density_and_seed():
    a = Maze.random(20, 20, density=0.3, seed=42)
    b = Maze.random(20, 20, density=0.3, seed=42)
    assert (a.grid == b.grid).all()                 # same seed, same maze
    assert a.is_walkable(a.start) and a.is_walkable(a.goal)
    walls = 400 - a.total_walkable()
    assert 60 < walls < 180                          # roughly 30%


def test_dict_round_trip():
    m = Maze.random(8, 8, density=0.2, seed=1)
    copy = Maze.from_dict(m.to_dict())
    assert (copy.grid == m.grid).all()
    assert copy.start == m.start and copy.goal == m.goal