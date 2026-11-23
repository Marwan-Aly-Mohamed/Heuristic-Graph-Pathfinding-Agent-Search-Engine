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


# ---------- step 7.4: playback ----------
def main_button(at, label):
    return next(b for b in at.button if b.label == label)


def main_slider(at, label):
    return next(s for s in at.slider if s.label == label)


def run_on_empty_maze(at, compare=False, rows=20, cols=30):
    from core.maze import Maze
    at.session_state["maze"] = Maze(rows, cols)
    label = "Compare both algorithms" if compare else "Run selected algorithm"
    find_button(at, label).click().run()
    assert not at.exception


def test_after_a_run_the_slider_shows_the_finished_search():
    at = make_app().run()
    run_on_empty_maze(at)
    res = at.session_state["results"][0]
    slider = main_slider(at, "Step")
    assert slider.value == len(res.steps) and slider.max == len(res.steps)
    assert len(at.success) == 1 and len(at.info) == 0


def test_scrubbing_to_the_middle_shows_progress_text():
    at = make_app().run()
    run_on_empty_maze(at)
    main_slider(at, "Step").set_value(3).run()
    assert not at.exception
    assert len(at.success) == 0 and len(at.info) == 1
    assert "3 nodes expanded" in at.info[0].value


def test_step_zero_shows_no_nodes_expanded():
    at = make_app().run()
    run_on_empty_maze(at)
    main_slider(at, "Step").set_value(0).run()
    assert "0 nodes expanded" in at.info[0].value


def test_compare_slider_uses_the_longer_search_and_finishes_astar_first():
    at = make_app().run()
    run_on_empty_maze(at, compare=True)
    astar_res, dijkstra_res = at.session_state["results"]
    assert main_slider(at, "Step").max == len(dijkstra_res.steps)
    main_slider(at, "Step").set_value(len(astar_res.steps) + 5).run()
    assert len(at.success) == 1      # A* has finished ...
    assert len(at.info) == 1         # ... Dijkstra is still searching


def test_navigation_buttons():
    at = make_app().run()
    run_on_empty_maze(at)
    total = at.session_state["results"][0].expanded_nodes
    main_button(at, "<< Start").click().run()
    assert main_slider(at, "Step").value == 0
    main_button(at, "Next >").click().run()
    main_button(at, "Next >").click().run()
    assert main_slider(at, "Step").value == 2
    main_button(at, "< Back").click().run()
    assert main_slider(at, "Step").value == 1
    main_button(at, "End >>").click().run()
    assert main_slider(at, "Step").value == total


def test_back_and_next_stop_at_the_ends():
    at = make_app().run()
    run_on_empty_maze(at)
    total = main_slider(at, "Step").max
    main_button(at, "End >>").click().run()
    main_button(at, "Next >").click().run()
    assert main_slider(at, "Step").value == total          # cannot go past the end
    main_button(at, "<< Start").click().run()
    main_button(at, "< Back").click().run()
    assert main_slider(at, "Step").value == 0              # cannot go below 0


def test_a_new_run_resets_the_slider_to_the_end():
    at = make_app().run()
    run_on_empty_maze(at)
    main_slider(at, "Step").set_value(2).run()
    find_button(at, "Run selected algorithm").click().run()
    res = at.session_state["results"][0]
    assert main_slider(at, "Step").value == len(res.steps)


def test_play_runs_to_the_end_without_errors():
    at = make_app().run()
    run_on_empty_maze(at, rows=5, cols=5)
    main_slider(at, "Play speed").set_value(10).run()
    main_button(at, "Play").click().run()
    assert not at.exception
    total = at.session_state["results"][0].expanded_nodes
    assert main_slider(at, "Step").value == total          # ended on the final picture
    assert len(at.success) == 1
    assert at.session_state["playing"] is False


def test_play_works_in_compare_mode():
    at = make_app().run()
    run_on_empty_maze(at, compare=True, rows=5, cols=5)
    main_slider(at, "Play speed").set_value(10).run()
    main_button(at, "Play").click().run()
    assert not at.exception
    assert len(at.success) == 2


def test_no_playback_controls_without_results():
    at = make_app().run()
    assert "Play" not in [b.label for b in at.button]
    assert "Step" not in [s.label for s in at.slider]


# ---------- step 7.5: dashboard ----------
def test_dashboard_is_absent_before_running():
    at = make_app().run()
    assert len(at.metric) == 0 and len(at.dataframe) == 0


def test_single_run_shows_five_metric_tiles():
    at = make_app().run()
    run_on_empty_maze(at)
    tiles = {m.label: m.value for m in at.metric}
    assert list(tiles) == ["Execution time", "Path length", "Expanded nodes",
                           "Explored density", "Path found"]
    assert tiles["Path length"] == "48 moves"
    assert tiles["Path found"] == "Yes"
    assert tiles["Execution time"].endswith(" ms")
    assert tiles["Explored density"].endswith(" %")


def test_failed_run_shows_dash_and_no():
    at = make_app().run()
    maze = at.session_state["maze"]
    maze.clear_walls()
    for r in range(maze.rows):
        maze.add_wall((r, 5))
    find_button(at, "Run selected algorithm").click().run()
    tiles = {m.label: m.value for m in at.metric}
    assert tiles["Path length"] == "-" and tiles["Path found"] == "No"


def test_compare_shows_table_charts_and_summary():
    at = make_app().run()
    run_on_empty_maze(at, compare=True)
    assert not at.exception
    assert len(at.dataframe) == 1
    table = at.dataframe[0].value
    assert list(table["Algorithm"]) == ["A*", "Dijkstra"]
    assert table["Path length (moves)"].nunique() == 1          # same cost for both
    summaries = [m.value for m in at.markdown if m.value.startswith("**Summary:**")]
    assert len(summaries) == 1 and "fewer" in summaries[0]


def test_dashboard_stays_visible_while_scrubbing():
    at = make_app().run()
    run_on_empty_maze(at, compare=True)
    main_slider(at, "Step").set_value(3).run()
    assert not at.exception
    assert len(at.dataframe) == 1


def test_compare_draws_three_charts_and_single_run_draws_none():
    at = make_app().run()
    run_on_empty_maze(at, compare=True)
    assert len(at.get("vega_lite_chart")) == 3
    run_on_empty_maze(at)                                    # now a single run
    assert len(at.get("vega_lite_chart")) == 0