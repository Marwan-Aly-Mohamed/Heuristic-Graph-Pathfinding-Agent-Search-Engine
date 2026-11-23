from core.maze import Maze
from core.pathfinding import compare_algorithms, format_table

print("=== 50x50 maze, 25% walls ===")
maze = Maze.random(50, 50, density=0.25, seed=3)
print(format_table(compare_algorithms(maze)[1]))

print("\n=== 100x100 empty maze ===")
print(format_table(compare_algorithms(Maze(100, 100))[1]))

print("\n=== Unreachable goal ===")
blocked = Maze(20, 20)
for r in range(20):
    blocked.add_wall((r, 10))
print(format_table(compare_algorithms(blocked)[1]))