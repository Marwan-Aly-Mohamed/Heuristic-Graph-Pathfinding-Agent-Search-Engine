"""Turns a SearchResult into the numbers we report and export."""


def explored_density(expanded_nodes, total_walkable):
    """Explored Node Density = expanded / total walkable cells * 100."""
    if total_walkable == 0:
        return 0.0
    return expanded_nodes / total_walkable * 100


def build_metrics(result, maze):
    """One flat dictionary per run (easy to show in a table and write to CSV)."""
    total_walkable = maze.total_walkable()
    return {
        "algorithm": result.algorithm,
        "path_found": result.found,
        "path_length": result.path_length if result.found else None,
        "runtime_ms": result.runtime_seconds * 1000,
        "expanded_nodes": result.expanded_nodes,
        "total_walkable_cells": total_walkable,
        "explored_density_percent": explored_density(result.expanded_nodes, total_walkable),
        "error": result.error,
    }