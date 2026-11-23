"""Maze editing logic for the UI. No Streamlit code in here, so it is easy to test."""

from core.maze import EMPTY, WALL

TOOLS = ["Draw wall", "Erase wall", "Set start", "Set goal"]


def cell_from_click(click, rows, cols):
    """Convert a click on the picture into a (row, col) cell.

    click = {"x", "y", "width", "height", ...} in pixels, where width/height are the
    size the picture is DISPLAYED at. Using fractions (x / width) keeps it correct
    even if the browser scales the picture."""
    if not click:
        return None
    width, height = click.get("width"), click.get("height")
    if not width or not height:
        return None
    col = int(click["x"] / width * cols)
    row = int(click["y"] / height * rows)
    col = min(max(col, 0), cols - 1)       # clicks on the very edge stay inside the grid
    row = min(max(row, 0), rows - 1)
    return (row, col)


def apply_tool(maze, tool, cell):
    """Apply one editing tool to one cell.
    Returns (changed, message). `message` is only filled when the click was refused."""
    if tool not in TOOLS:
        raise ValueError(f"Unknown tool '{tool}'.")
    if not maze.in_bounds(cell):
        return False, "That cell is outside the grid."

    if tool == "Draw wall":
        if cell == maze.start or cell == maze.goal:
            return False, "You can't put a wall on the start or the goal."
        if maze.grid[cell] == WALL:
            return False, ""
        maze.add_wall(cell)
        return True, ""

    if tool == "Erase wall":
        if maze.grid[cell] == EMPTY:
            return False, ""
        maze.remove_wall(cell)
        return True, ""

    # Set start / Set goal
    moving_start = tool == "Set start"
    current = maze.start if moving_start else maze.goal
    other = maze.goal if moving_start else maze.start
    if cell == other:
        return False, "The start and the goal can't be on the same cell."
    if cell == current:
        return False, ""
    maze.remove_wall(cell)                 # moving onto a wall clears that wall
    if moving_start:
        maze.set_start(cell)
    else:
        maze.set_goal(cell)
    return True, ""


def handle_click(maze, click, tool, last_click_id):
    """Process the value returned by the click component.

    Streamlit reruns the script often, and the component keeps returning the SAME old
    click until a new one happens. So we remember the click's time stamp and ignore
    clicks we have already used.
    Returns (changed, message, new_last_click_id)."""
    if not click:
        return False, "", last_click_id
    click_id = click.get("unix_time")
    if click_id == last_click_id:
        return False, "", last_click_id
    cell = cell_from_click(click, maze.rows, maze.cols)
    if cell is None:
        return False, "", click_id
    changed, message = apply_tool(maze, tool, cell)
    return changed, message, click_id