"""Result type and helper shared by BOTH algorithms."""

from dataclasses import dataclass, field


@dataclass
class SearchResult:
    algorithm: str
    found: bool = False
    path: list = field(default_factory=list)    # [(r, c), ...] from start to goal
    path_length: int = 0                         # number of MOVES (cells - 1)
    expanded_nodes: int = 0                      # nodes popped and processed
    steps: list = field(default_factory=list)    # replay log: (expanded_node, [pushed_nodes])
    runtime_seconds: float = 0.0                 # set by run_search()
    error: str = ""                              # e.g. "Start is on a wall"


def reconstruct_path(came_from, goal):
    """Walk backward from goal to start using came_from, then reverse."""
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path