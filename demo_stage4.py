from algorithms.astar import astar
from algorithms.dijkstra import dijkstra
from core.maze import Maze


def draw(maze, result):
    explored = {node for node, _ in result.steps}
    path = set(result.path)
    for r in range(maze.rows):
        line = ""
        for c in range(maze.cols):
            p = (r, c)
            if p == maze.start: line += "S "
            elif p == maze.goal: line += "G "
            elif maze.grid[r, c] == 1: line += "# "
            elif p in path: line += "* "
            elif p in explored: line += "o "
            else: line += ". "
        print(line)


maze = Maze.random(10, 20, density=0.2, seed=3)
for algo in (astar, dijkstra):
    res = algo(maze)
    print(f"\n{res.algorithm}: found={res.found} path={res.path_length} expanded={res.expanded_nodes}")
    draw(maze, res)