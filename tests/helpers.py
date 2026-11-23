"""Helpers shared by the algorithm tests."""

from collections import deque


def bfs_shortest_moves(maze):
    """Independent 'referee': plain BFS gives the true shortest distance
    on an unweighted grid. Returns None if unreachable."""
    queue = deque([(maze.start, 0)])
    seen = {maze.start}
    while queue:
        pos, dist = queue.popleft()
        if pos == maze.goal:
            return dist
        for nb in maze.neighbors(pos):
            if nb not in seen:
                seen.add(nb)
                queue.append((nb, dist + 1))
    return None


def assert_valid_path(maze, result):
    path = result.path
    assert path[0] == maze.start
    assert path[-1] == maze.goal
    assert result.path_length == len(path) - 1
    for cell in path:
        assert maze.is_walkable(cell), f"{cell} is a wall or outside"
    for a, b in zip(path, path[1:]):
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1, f"{a} -> {b} is not a single move"