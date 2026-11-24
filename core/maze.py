"""Maze / grid system.

Grid values:  0 = empty (walkable),  1 = wall (obstacle).
Positions are (row, col) tuples. Row 0 is the top of the grid.
"""

import random

import numpy as np

EMPTY = 0
WALL = 1

# Up, Down, Left, Right  (as (row_change, col_change))
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

MAX_SIZE = 100  # keeps the app light on a low-spec laptop; change if needed

# Difficulty presets = fraction of cells that become walls
DIFFICULTY_LEVELS = {"Easy": 0.10, "Medium": 0.25, "Hard": 0.40}
DIFFICULTY_OPTIONS = list(DIFFICULTY_LEVELS) + ["Custom"]


class Maze:
    def __init__(self, rows, cols, start=None, goal=None):
        if not (1 <= rows <= MAX_SIZE and 1 <= cols <= MAX_SIZE):
            raise ValueError(f"Grid size must be between 1 and {MAX_SIZE}.")
        self.rows = rows
        self.cols = cols
        self.grid = np.zeros((rows, cols), dtype=np.int8)  # all empty
        self.start = start if start is not None else (0, 0)
        self.goal = goal if goal is not None else (rows - 1, cols - 1)

    # ---------- checking positions ----------
    def in_bounds(self, pos):
        r, c = pos
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_walkable(self, pos):
        return self.in_bounds(pos) and self.grid[pos] == EMPTY

    # ---------- editing the maze ----------
    def add_wall(self, pos):
        if not self.in_bounds(pos):
            raise ValueError(f"{pos} is outside the grid.")
        if pos == self.start or pos == self.goal:
            raise ValueError("Cannot put a wall on the start or goal.")
        self.grid[pos] = WALL

    def remove_wall(self, pos):
        if not self.in_bounds(pos):
            raise ValueError(f"{pos} is outside the grid.")
        self.grid[pos] = EMPTY

    def toggle_wall(self, pos):
        """Used later by the UI: click a cell to flip it."""
        if self.grid[pos] == WALL:
            self.remove_wall(pos)
        else:
            self.add_wall(pos)

    def signature(self):
        """A value that changes whenever the grid, start or goal changes.
        The UI uses it to know when old search results no longer match the maze."""
        return (self.rows, self.cols, self.start, self.goal, self.grid.tobytes())

    def clear_walls(self):
        """Remove every wall (start and goal stay where they are)."""
        self.grid[:] = EMPTY

    def set_start(self, pos):
        if not self.is_walkable(pos):
            raise ValueError(f"Start {pos} must be inside the grid and not a wall.")
        self.start = pos

    def set_goal(self, pos):
        if not self.is_walkable(pos):
            raise ValueError(f"Goal {pos} must be inside the grid and not a wall.")
        self.goal = pos

    # ---------- used by the algorithms ----------
    def neighbors(self, pos):
        """Walkable cells reachable in ONE move (up/down/left/right)."""
        r, c = pos
        result = []
        for dr, dc in DIRECTIONS:
            nxt = (r + dr, c + dc)
            if self.is_walkable(nxt):
                result.append(nxt)
        return result

    def total_walkable(self):
        """Number of empty cells (used for explored-node density)."""
        return int(np.count_nonzero(self.grid == EMPTY))

    def validate(self):
        """Return an error message if start/goal are invalid, else None.
        Both algorithms call this first."""
        if not self.in_bounds(self.start):
            return f"Start {self.start} is outside the grid."
        if not self.in_bounds(self.goal):
            return f"Goal {self.goal} is outside the grid."
        if self.grid[self.start] == WALL:
            return f"Start {self.start} is on a wall."
        if self.grid[self.goal] == WALL:
            return f"Goal {self.goal} is on a wall."
        return None

    # ---------- random generation ----------
    @classmethod
    def random(cls, rows, cols, density=0.25, start=None, goal=None, seed=None):
        """density = fraction of cells that become walls (0.0 to 0.9).
        Start and goal are always kept free.
        NOTE: it does NOT guarantee a path exists - that is realistic,
        and lets us test unreachable goals."""
        if not 0.0 <= density <= 0.9:
            raise ValueError("Density must be between 0.0 and 0.9.")
        maze = cls(rows, cols, start, goal)
        rng = random.Random(seed)  # same seed -> same maze (good for tests)
        for r in range(rows):
            for c in range(cols):
                pos = (r, c)
                if pos != maze.start and pos != maze.goal and rng.random() < density:
                    maze.grid[pos] = WALL
        return maze


    def has_path(self):
        """True if the goal can be reached from the start (simple flood fill).
        This is deliberately NOT A* or Dijkstra, so it can act as an independent check."""
        if self.validate() is not None:
            return False
        seen = {self.start}
        stack = [self.start]
        while stack:
            pos = stack.pop()
            if pos == self.goal:
                return True
            for nb in self.neighbors(pos):
                if nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        return False

    @classmethod
    def random_solvable(cls, rows, cols, density=0.25, seed=0, max_tries=200):
        """Try seeds seed, seed+1, seed+2 ... until the goal is reachable.
        Returns (maze, seed_used), or (None, None) if nothing worked."""
        for i in range(max_tries):
            maze = cls.random(rows, cols, density, seed=seed + i)
            if maze.has_path():
                return maze, seed + i
        return None, None

    
    # ---------- saving (needed for JSON export in Stage 8) ----------
    def to_dict(self):
        return {
            "rows": self.rows,
            "cols": self.cols,
            "start": list(self.start),
            "goal": list(self.goal),
            "grid": self.grid.tolist(),
        }

    @classmethod
    def from_dict(cls, data):
        maze = cls(data["rows"], data["cols"], tuple(data["start"]), tuple(data["goal"]))
        maze.grid = np.array(data["grid"], dtype=np.int8)
        return maze

    def __str__(self):
        """Text picture: S=start, G=goal, #=wall, .=empty"""
        lines = []
        for r in range(self.rows):
            row = ""
            for c in range(self.cols):
                if (r, c) == self.start:
                    row += "S "
                elif (r, c) == self.goal:
                    row += "G "
                elif self.grid[r, c] == WALL:
                    row += "# "
                else:
                    row += ". "
            lines.append(row)
        return "\n".join(lines)