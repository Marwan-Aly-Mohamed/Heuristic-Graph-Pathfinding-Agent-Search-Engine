from core.maze import Maze
from core.pathfinding import compare_algorithms
from visualization.visualizer import make_figure, save_gif

maze = Maze.random(25, 40, density=0.28, seed=2)
results, rows = compare_algorithms(maze, repeats=3)

# 1) Side-by-side picture of the finished searches
fig = make_figure(maze, results)
fig.savefig("exports/comparison.png", dpi=110)

# 2) A picture halfway through the search (shows explored + waiting cells)
half = len(results[1].steps) // 2
make_figure(maze, results[1], step=half).savefig("exports/dijkstra_halfway.png", dpi=110)

# 3) Animated GIFs
for res in results:
    name = res.algorithm.replace("*", "star").lower()
    frames = save_gif(maze, res, f"exports/{name}.gif", cell_px=10)
    print(f"exports/{name}.gif  ({frames} frames)")

print("Saved PNGs and GIFs in exports/")