from algorithms.astar import astar
from core.maze import Maze

maze = Maze.random(8, 12, density=0.25, seed=3)
result = astar(maze)
print("found:", result.found, "| path length:", result.path_length,
      "| expanded:", result.expanded_nodes)

path = set(result.path)
for r in range(maze.rows):
    line = ""
    for c in range(maze.cols):
        p = (r, c)
        if p == maze.start: line += "S "
        elif p == maze.goal: line += "G "
        elif maze.grid[r, c] == 1: line += "# "
        elif p in path: line += "* "
        else: line += ". "
    print(line)