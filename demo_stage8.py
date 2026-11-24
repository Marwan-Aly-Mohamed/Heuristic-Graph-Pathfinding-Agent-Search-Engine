import json

from core.exporter import save_exports
from core.maze import Maze
from core.pathfinding import compare_algorithms

maze, seed = Maze.random_solvable(25, 40, density=0.28, seed=2)
results, _ = compare_algorithms(maze, repeats=3)

paths = save_exports(maze, results, folder="exports", name="demo_results")
print("Written:", paths)

print("\n--- CSV ---")
print(open(paths["csv"], encoding="utf-8").read())

data = json.load(open(paths["json"], encoding="utf-8"))
print("--- JSON summary ---")
print("top-level keys:", list(data))
print("maze:", data["maze"]["rows"], "x", data["maze"]["cols"], "start", data["maze"]["start"], "goal", data["maze"]["goal"])
for run in data["runs"]:
    print(run["algorithm"], "| path cells:", len(run["path"]), "| logged steps:", len(run["steps"]))