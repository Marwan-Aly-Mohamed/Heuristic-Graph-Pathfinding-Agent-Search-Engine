import pytest

from algorithms.astar import astar
from core.editor import TOOLS, apply_tool, cell_from_click, handle_click
from core.maze import Maze


def click_at(x, y, width=200, height=100, t=1):
    return {"x": x, "y": y, "width": width, "height": height, "unix_time": t}


# ---------- pixel -> cell ----------
def test_cell_from_click_basic_corners():
    # picture 200 x 100 px, grid 10 rows x 20 cols -> every cell is 10 x 10 px
    assert cell_from_click(click_at(0, 0), 10, 20) == (0, 0)
    assert cell_from_click(click_at(15, 25), 10, 20) == (2, 1)
    assert cell_from_click(click_at(199, 99), 10, 20) == (9, 19)


def test_cell_from_click_edge_is_clamped():
    assert cell_from_click(click_at(200, 100), 10, 20) == (9, 19)
    assert cell_from_click(click_at(-3, -3), 10, 20) == (0, 0)


def test_cell_from_click_works_when_browser_scales_the_picture():
    # same grid, but the picture is displayed at HALF size (100 x 50)
    assert cell_from_click(click_at(15, 12, width=100, height=50), 10, 20) == (2, 3)


def test_cell_from_click_handles_missing_data():
    assert cell_from_click(None, 10, 20) is None
    assert cell_from_click({"x": 1, "y": 1}, 10, 20) is None
    assert cell_from_click({"x": 1, "y": 1, "width": 0, "height": 0}, 10, 20) is None


# ---------- tools ----------
def test_draw_and_erase_wall():
    m = Maze(5, 5)
    assert apply_tool(m, "Draw wall", (2, 2)) == (True, "")
    assert not m.is_walkable((2, 2))
    assert apply_tool(m, "Draw wall", (2, 2)) == (False, "")     # already a wall
    assert apply_tool(m, "Erase wall", (2, 2)) == (True, "")
    assert m.is_walkable((2, 2))
    assert apply_tool(m, "Erase wall", (2, 2)) == (False, "")    # already empty


def test_cannot_draw_wall_on_start_or_goal():
    m = Maze(5, 5)
    for cell in (m.start, m.goal):
        changed, msg = apply_tool(m, "Draw wall", cell)
        assert not changed and msg
        assert m.is_walkable(cell)


def test_set_start_and_goal():
    m = Maze(5, 5)
    assert apply_tool(m, "Set start", (1, 1)) == (True, "")
    assert m.start == (1, 1)
    assert apply_tool(m, "Set goal", (3, 3)) == (True, "")
    assert m.goal == (3, 3)


def test_set_start_on_a_wall_clears_the_wall():
    m = Maze(5, 5)
    m.add_wall((2, 2))
    assert apply_tool(m, "Set start", (2, 2)) == (True, "")
    assert m.start == (2, 2) and m.is_walkable((2, 2))


def test_start_and_goal_cannot_share_a_cell():
    m = Maze(5, 5)
    changed, msg = apply_tool(m, "Set start", m.goal)
    assert not changed and msg and m.start == (0, 0)
    changed, msg = apply_tool(m, "Set goal", m.start)
    assert not changed and msg and m.goal == (4, 4)


def test_clicking_the_current_start_again_changes_nothing():
    m = Maze(5, 5)
    assert apply_tool(m, "Set start", m.start) == (False, "")


def test_outside_cell_and_unknown_tool():
    m = Maze(5, 5)
    changed, msg = apply_tool(m, "Draw wall", (9, 9))
    assert not changed and msg
    with pytest.raises(ValueError):
        apply_tool(m, "Paint", (1, 1))


def test_tools_list_matches_what_apply_tool_accepts():
    m = Maze(5, 5)
    for tool in TOOLS:
        apply_tool(m, tool, (2, 2))          # must not raise


# ---------- click bookkeeping ----------
def test_handle_click_applies_a_new_click_once():
    m = Maze(10, 20)
    click = click_at(15, 25, t=111)
    changed, msg, last = handle_click(m, click, "Draw wall", None)
    assert changed and last == 111 and not m.is_walkable((2, 1))

    m.remove_wall((2, 1))                    # undo it by hand
    changed, msg, last = handle_click(m, click, "Draw wall", last)   # SAME click again
    assert not changed and m.is_walkable((2, 1))                     # ignored


def test_handle_click_new_timestamp_is_applied():
    m = Maze(10, 20)
    _, _, last = handle_click(m, click_at(15, 25, t=1), "Draw wall", None)
    changed, _, last = handle_click(m, click_at(35, 25, t=2), "Draw wall", last)
    assert changed and last == 2 and not m.is_walkable((2, 3))


def test_handle_click_without_click():
    m = Maze(10, 20)
    assert handle_click(m, None, "Draw wall", 5) == (False, "", 5)


def test_handle_click_returns_refusal_message():
    m = Maze(10, 20)                         # start is (0, 0)
    changed, msg, _ = handle_click(m, click_at(1, 1, t=3), "Draw wall", None)
    assert not changed and msg


# ---------- edited mazes still work with the algorithms ----------
def test_edited_maze_is_solved_through_the_gap():
    m = Maze(7, 7, start=(3, 0), goal=(3, 6))
    for r in range(7):
        if r != 5:                           # wall column with one gap at row 5
            apply_tool(m, "Draw wall", (r, 3))
    res = astar(m)
    assert res.found and (5, 3) in res.path
    apply_tool(m, "Draw wall", (5, 3))       # close the gap
    assert not astar(m).found


def test_clear_walls():
    m = Maze.random(10, 10, 0.4, seed=1)
    m.clear_walls()
    assert m.total_walkable() == 100 and m.start == (0, 0)