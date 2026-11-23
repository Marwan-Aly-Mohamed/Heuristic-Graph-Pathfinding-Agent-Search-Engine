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


# (key in the metrics row, label shown to the user)
DISPLAY_COLUMNS = [
    ("algorithm", "Algorithm"),
    ("path_found", "Path found"),
    ("path_length", "Path length (moves)"),
    ("runtime_ms", "Execution time (ms)"),
    ("expanded_nodes", "Expanded nodes"),
    ("explored_density_percent", "Explored density (%)"),
    ("total_walkable_cells", "Walkable cells"),
]


def display_rows(rows):
    """Same data with friendly column names and rounded numbers, for tables and charts."""
    shown = []
    for row in rows:
        item = {label: row[key] for key, label in DISPLAY_COLUMNS}
        item["Path found"] = "Yes" if row["path_found"] else "No"
        item["Execution time (ms)"] = round(row["runtime_ms"], 3)
        item["Explored density (%)"] = round(row["explored_density_percent"], 2)
        shown.append(item)
    return shown


def compare_summary(rows):
    """One short paragraph comparing A* with Dijkstra. Returns "" if either is missing."""
    by_name = {row["algorithm"]: row for row in rows}
    if "A*" not in by_name or "Dijkstra" not in by_name:
        return ""
    a, d = by_name["A*"], by_name["Dijkstra"]

    if not a["path_found"] and not d["path_found"]:
        if a["expanded_nodes"] == d["expanded_nodes"]:
            return (f"Neither algorithm found a path. Both had to explore the same "
                    f"{a['expanded_nodes']} cells before giving up, so the heuristic gave no advantage.")
        return (f"Neither algorithm found a path. A* expanded {a['expanded_nodes']} nodes, "
                f"Dijkstra {d['expanded_nodes']}.")
    if a["path_found"] != d["path_found"]:
        winner = "A*" if a["path_found"] else "Dijkstra"
        return f"Only {winner} found a path."

    parts = []
    if a["path_length"] == d["path_length"]:
        parts.append(f"Both found a shortest path of {a['path_length']} moves.")
    else:
        parts.append(f"The path lengths differ: A* {a['path_length']}, Dijkstra {d['path_length']}.")

    a_exp, d_exp = a["expanded_nodes"], d["expanded_nodes"]
    if a_exp < d_exp:
        fewer = (1 - a_exp / d_exp) * 100
        parts.append(f"A* expanded {a_exp} nodes versus {d_exp} for Dijkstra ({fewer:.0f}% fewer).")
    elif a_exp == d_exp:
        parts.append(f"Both expanded {a_exp} nodes.")
    else:
        parts.append(f"A* expanded {a_exp} nodes versus {d_exp} for Dijkstra.")

    a_ms, d_ms = a["runtime_ms"], d["runtime_ms"]
    if a_ms > 0 and d_ms > 0:
        if a_ms <= d_ms:
            parts.append(f"A* was {d_ms / a_ms:.1f}x faster.")
        else:
            parts.append(f"A* was {a_ms / d_ms:.1f}x slower here, because computing the "
                         f"heuristic costs extra time for every node.")
    return " ".join(parts)