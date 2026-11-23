"""Dijkstra's algorithm, written from scratch (only heapq is used)."""

import heapq

from core.result import SearchResult, reconstruct_path


def dijkstra(maze):
    error = maze.validate()
    if error:
        return SearchResult(algorithm="Dijkstra", error=error)

    start, goal = maze.start, maze.goal

    cost = {start: 0}            # best known cost from start to each node
    came_from = {start: None}
    closed = set()
    steps = []
    expanded = 0

    # Queue items: (cost, node). Lowest cost is popped first.
    # No heuristic: Dijkstra knows nothing about where the goal is.
    queue = [(0, start)]

    while queue:
        _, current = heapq.heappop(queue)

        if current in closed:    # stale duplicate -> skip, do NOT count
            continue
        closed.add(current)
        expanded += 1
        pushed = []

        if current == goal:
            steps.append((current, pushed))
            path = reconstruct_path(came_from, goal)
            return SearchResult(
                algorithm="Dijkstra", found=True, path=path,
                path_length=len(path) - 1, expanded_nodes=expanded, steps=steps,
            )

        for neighbor in maze.neighbors(current):
            new_cost = cost[current] + 1
            if neighbor not in cost or new_cost < cost[neighbor]:
                cost[neighbor] = new_cost
                came_from[neighbor] = current
                heapq.heappush(queue, (new_cost, neighbor))
                pushed.append(neighbor)

        steps.append((current, pushed))

    return SearchResult(algorithm="Dijkstra", expanded_nodes=expanded, steps=steps, error="No path exists.")