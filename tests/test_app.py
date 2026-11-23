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