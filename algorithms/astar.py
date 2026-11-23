"""A* Search, written from scratch (only heapq is used, for the priority queue)."""

import heapq

from core.result import SearchResult, reconstruct_path


def manhattan(a, b):
    """Heuristic h: minimum possible moves between two cells (4-direction grid)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(maze):
    error = maze.validate()
    if error:
        return SearchResult(algorithm="A*", error=error)

    start, goal = maze.start, maze.goal

    g_cost = {start: 0}          # best known cost from start to each node
    came_from = {start: None}    # who we came from (to rebuild the path)
    closed = set()               # nodes already expanded
    steps = []                   # log for the visualizer
    expanded = 0

    # Queue items: (f, h, node). Lowest f is popped first.
    # On a tie in f, the smaller h wins (the node closer to the goal).
    queue = [(manhattan(start, goal), manhattan(start, goal), start)]

    while queue:
        _, _, current = heapq.heappop(queue)

        if current in closed:    # stale duplicate entry -> skip, do NOT count
            continue
        closed.add(current)
        expanded += 1
        pushed = []

        if current == goal:
            steps.append((current, pushed))
            path = reconstruct_path(came_from, goal)
            return SearchResult(
                algorithm="A*", found=True, path=path,
                path_length=len(path) - 1, expanded_nodes=expanded, steps=steps,
            )

        for neighbor in maze.neighbors(current):
            new_g = g_cost[current] + 1          # every move costs 1
            if neighbor not in g_cost or new_g < g_cost[neighbor]:
                g_cost[neighbor] = new_g
                came_from[neighbor] = current
                h = manhattan(neighbor, goal)
                heapq.heappush(queue, (new_g + h, h, neighbor))
                pushed.append(neighbor)

        steps.append((current, pushed))

    # Queue ran empty: goal can't be reached
    return SearchResult(algorithm="A*", expanded_nodes=expanded, steps=steps, error="No path exists.")