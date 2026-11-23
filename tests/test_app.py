"""Tests the Streamlit app without opening a browser (Streamlit's AppTest)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def make_app():
    return AppTest.from_file(APP, default_timeout=30)


def test_app_starts_without_errors():
    at = make_app().run()
    assert not at.exception
    maze = at.session_state["maze"]
    assert (maze.rows, maze.cols) == (20, 30)


def test_generate_button_uses_sidebar_settings():
    at = make_app().run()
    at.sidebar.slider[0].set_value(12)          # rows
    at.sidebar.slider[1].set_value(15)          # columns
    at.sidebar.slider[2].set_value(0.0)         # density
    at.sidebar.button[0].click().run()
    assert not at.exception
    maze = at.session_state["maze"]
    assert (maze.rows, maze.cols) == (12, 15)
    assert maze.total_walkable() == 12 * 15     # density 0 -> no walls


def test_changing_sliders_alone_does_not_replace_the_maze():
    at = make_app().run()
    before = at.session_state["maze"]
    at.sidebar.slider[0].set_value(40).run()    # moving a slider is not a click
    assert at.session_state["maze"] is before


def test_editor_controls_exist():
    from core.editor import TOOLS
    at = make_app().run()
    assert not at.exception
    assert at.sidebar.radio[0].options == TOOLS


def test_clear_all_walls_button():
    at = make_app().run()
    maze = at.session_state["maze"]
    assert maze.total_walkable() < maze.rows * maze.cols       # starts with some walls
    at.sidebar.button[1].click().run()
    assert not at.exception
    maze = at.session_state["maze"]
    assert maze.total_walkable() == maze.rows * maze.cols


def test_changing_the_tool_does_not_change_the_maze():
    at = make_app().run()
    before = at.session_state["maze"].grid.copy()
    at.sidebar.radio[0].set_value("Set goal").run()
    assert not at.exception
    assert (at.session_state["maze"].grid == before).all()


# ---------- step 7.3: algorithms ----------
def find_button(at, label):
    return next(b for b in at.sidebar.button if b.label == label)


def find_radio(at, label):
    return next(r for r in at.sidebar.radio if r.label == label)


def open_maze(at):
    """Replace the maze with an empty one (so a path surely exists)."""
    at.session_state["maze"].clear_walls()


def test_no_results_before_running():
    at = make_app().run()
    assert at.session_state["results"] is None


def test_run_astar_shows_a_found_path():
    at = make_app().run()
    open_maze(at)
    find_button(at, "Run selected algorithm").click().run()
    assert not at.exception
    results = at.session_state["results"]
    assert len(results) == 1 and results[0].algorithm == "A*"
    assert results[0].found and results[0].path_length == 19 + 29
    assert len(at.success) == 1


def test_run_dijkstra_when_selected():
    at = make_app().run()
    open_maze(at)
    find_radio(at, "Algorithm").set_value("Dijkstra").run()
    assert at.session_state["results"] is None              # choosing does not run
    find_button(at, "Run selected algorithm").click().run()
    assert at.session_state["results"][0].algorithm == "Dijkstra"


def test_compare_runs_both_on_the_same_maze():
    at = make_app().run()
    open_maze(at)
    find_button(at, "Compare both algorithms").click().run()
    assert not at.exception
    a, d = at.session_state["results"]
    assert (a.algorithm, d.algorithm) == ("A*", "Dijkstra")
    assert a.path_length == d.path_length
    assert a.expanded_nodes <= d.expanded_nodes
    assert len(at.success) == 2


def test_unreachable_goal_shows_an_error_message():
    at = make_app().run()
    maze = at.session_state["maze"]
    maze.clear_walls()
    for r in range(maze.rows):
        maze.add_wall((r, 5))                                # full wall column
    find_button(at, "Run selected algorithm").click().run()
    assert not at.exception
    assert not at.session_state["results"][0].found
    assert len(at.error) == 1


def test_results_are_cleared_when_the_maze_changes():
    at = make_app().run()
    open_maze(at)
    find_button(at, "Run selected algorithm").click().run()
    assert at.session_state["results"] is not None
    at.session_state["maze"].add_wall((5, 5))                # simulate an edit
    at.run()
    assert at.session_state["results"] is None
    assert len(at.info) == 1


def test_results_stay_when_nothing_changes():
    at = make_app().run()
    open_maze(at)
    find_button(at, "Run selected algorithm").click().run()
    at.sidebar.slider[2].set_value(0.4).run()                # unrelated slider
    assert at.session_state["results"] is not None