"""Streamlit app - Step 7.5: editor + run algorithms + playback + performance dashboard."""

import math
import time

import pandas as pd
import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates

from core.editor import TOOLS, handle_click
from core.maze import MAX_SIZE, Maze
from core.metrics import build_metrics, compare_summary, display_rows
from core.pathfinding import ALGORITHMS, compare_algorithms, run_search
from core.result import SearchResult
from visualization.visualizer import FRONTIER, codes_to_image, frame_codes

st.set_page_config(page_title="Pathfinding Agent", layout="wide")
st.title("Heuristic Graph Pathfinding Agent Search Engine")

MAX_PLAY_FRAMES = 120      # auto-play shows at most this many pictures


# ---------- small helper functions ----------
def set_step(value):
    """Button callback: jump to an exact step."""
    st.session_state.step_slider = value


def move_step(delta, max_steps):
    """Button callback: go one step back (-1) or forward (+1)."""
    new_step = st.session_state.step_slider + delta
    st.session_state.step_slider = min(max(new_step, 0), max_steps)


def start_play():
    """Button callback: ask the main script to play the animation from step 0."""
    st.session_state.playing = True
    st.session_state.step_slider = 0


def draw_frame(image_slot, text_slot, maze, res, step, cell_px):
    """Draw one algorithm's picture and status text for a given step."""
    codes = frame_codes(maze, res, step)
    image_slot.image(codes_to_image(codes, cell_px), width="stretch")
    if step >= len(res.steps):                    # this search has finished
        if res.found:
            text_slot.success(f"Path found: {res.path_length} moves, {res.expanded_nodes} nodes expanded")
        else:
            text_slot.error(f"No path found: {res.error} ({res.expanded_nodes} nodes expanded)")
    else:
        waiting = int((codes == FRONTIER).sum())
        text_slot.info(f"Searching... {step} nodes expanded, {waiting} waiting in the queue")


METRIC_HELP = """
- **Execution time**: measured with `time.perf_counter()` around the search only (median of the timing repeats).
- **Path length**: number of moves from start to goal.
- **Expanded nodes**: nodes taken out of the priority queue and processed. Stale duplicate entries are skipped and not counted. Same rule for both algorithms.
- **Explored density** = expanded nodes / total walkable cells x 100.
- **Path found**: whether the goal was reached.
"""


def render_dashboard(maze, results):
    """Metrics for the COMPLETE search: tiles for one run, table + charts for a comparison."""
    st.subheader("Performance dashboard")
    rows = [build_metrics(r, maze) for r in results]

    if len(rows) == 1:
        row = rows[0]
        st.markdown(f"**{row['algorithm']}**")
        t1, t2, t3, t4, t5 = st.columns(5)
        t1.metric("Execution time", f"{row['runtime_ms']:.3f} ms")
        t2.metric("Path length", f"{row['path_length']} moves" if row["path_found"] else "-")
        t3.metric("Expanded nodes", f"{row['expanded_nodes']}")
        t4.metric("Explored density", f"{row['explored_density_percent']:.2f} %")
        t5.metric("Path found", "Yes" if row["path_found"] else "No")
    else:
        table = pd.DataFrame(display_rows(rows))
        st.dataframe(table, hide_index=True, width="stretch")
        chart_columns = st.columns(3)
        for column, name in zip(chart_columns,
                                ["Expanded nodes", "Explored density (%)", "Execution time (ms)"]):
            column.markdown(f"**{name}**")
            column.bar_chart(table.set_index("Algorithm")[[name]], height=220)
        summary = compare_summary(rows)
        if summary:
            st.markdown(f"**Summary:** {summary}")

    with st.expander("How are these metrics calculated?"):
        st.markdown(METRIC_HELP)


# ---------- session state: memory that survives reruns ----------
if "maze" not in st.session_state:
    st.session_state.maze = Maze.random(20, 30, 0.25, seed=2)
if "last_click" not in st.session_state:
    st.session_state.last_click = None          # time stamp of the last click we used
if "results" not in st.session_state:
    st.session_state.results = None             # list of SearchResult (1 or 2)
    st.session_state.results_signature = None   # which maze those results belong to

maze = st.session_state.maze


def store_results(results):
    """Remember results, the maze they belong to, and show the finished search."""
    st.session_state.results = results
    st.session_state.results_signature = maze.signature()
    st.session_state.step_slider = max(len(r.steps) for r in results)


# ---------- sidebar ----------
with st.sidebar:
    st.header("Maze settings")
    rows = st.slider("Rows", 5, MAX_SIZE, 20)
    cols = st.slider("Columns", 5, MAX_SIZE, 30)
    density = st.slider("Obstacle density", 0.0, 0.6, 0.25, 0.05)
    seed = st.number_input("Random seed", min_value=0, max_value=99999, value=2, step=1)

    if st.button("Generate random maze"):
        st.session_state.maze = Maze.random(rows, cols, density, seed=int(seed))
        st.rerun()

    st.header("Maze editor")
    tool = st.radio("Click on the maze to...", TOOLS)

    if st.button("Clear all walls"):
        maze.clear_walls()
        st.rerun()

    st.header("Algorithm")
    algorithm = st.radio("Algorithm", list(ALGORITHMS))
    repeats = st.slider("Timing repeats", 1, 10, 3,
                        help="The search is repeated this many times and the median time is reported.")

    if st.button("Run selected algorithm"):
        store_results([run_search(maze, algorithm, repeats)])

    if st.button("Compare both algorithms"):
        results, _ = compare_algorithms(maze, repeats)
        store_results(results)

# ---------- main area 1: the clickable maze ----------
st.subheader("Maze")
codes = frame_codes(maze, SearchResult(algorithm=""))     # "no search yet"
cell_px = max(4, min(20, 800 // maze.cols))
image = codes_to_image(codes, cell_px)

click = streamlit_image_coordinates(
    image, key="maze_picture", width=image.shape[1], cursor="crosshair",
    png_compression_level=1,
)

changed, message, st.session_state.last_click = handle_click(
    maze, click, tool, st.session_state.last_click
)
if changed:
    st.rerun()                  # redraw the picture with the edit
if message:
    st.warning(message)

walls = maze.rows * maze.cols - maze.total_walkable()
st.caption(
    f"Grid {maze.rows} x {maze.cols} | walls: {walls} | walkable cells: {maze.total_walkable()} "
    f"| start {maze.start} | goal {maze.goal}"
)

# ---------- main area 2: search results ----------
st.subheader("Search results")

results = st.session_state.results
if results is not None and st.session_state.results_signature != maze.signature():
    st.session_state.results = None            # the maze changed -> old results are wrong
    results = None
    st.info("The maze was changed, so the old results were cleared. Run an algorithm again.")

if results is None:
    st.write("Choose an algorithm in the sidebar and press **Run**, or press **Compare**.")
else:
    max_steps = max(len(r.steps) for r in results)

    # Prepare the slider's value BEFORE the slider exists (Streamlit forbids changing it afterwards)
    if "step_slider" not in st.session_state:
        st.session_state.step_slider = max_steps
    if st.session_state.pop("jump_to_end", False):
        st.session_state.step_slider = max_steps
    st.session_state.step_slider = min(st.session_state.step_slider, max_steps)

    # --- playback controls ---
    b1, b2, b3, b4, b5 = st.columns(5)
    b1.button("<< Start", on_click=set_step, args=(0,))
    b2.button("< Back", on_click=move_step, args=(-1, max_steps))
    b3.button("Next >", on_click=move_step, args=(1, max_steps))
    b4.button("End >>", on_click=set_step, args=(max_steps,))
    b5.button("Play", on_click=start_play)

    c1, c2 = st.columns([3, 1])
    c1.slider("Step", 0, max(1, max_steps), key="step_slider")
    speed = c2.slider("Play speed", 1, 10, 5, key="play_speed")
    step = st.session_state.step_slider

    # --- one panel per algorithm (same step for both, so they can be compared) ---
    result_px = max(4, min(16, 600 // maze.cols))
    panels = st.columns(len(results))
    slots = []
    for panel, res in zip(panels, results):
        with panel:
            st.markdown(f"**{res.algorithm}**")
            slots.append((st.empty(), st.empty()))
    for (image_slot, text_slot), res in zip(slots, results):
        draw_frame(image_slot, text_slot, maze, res, step, result_px)

    render_dashboard(maze, results)

    # --- auto-play: redraw the panels again and again ---
    if st.session_state.get("playing"):
        st.session_state.playing = False
        stride = max(1, math.ceil(max_steps / MAX_PLAY_FRAMES))
        frames = list(range(0, max_steps, stride)) + [max_steps]
        for frame_step in frames:
            for (image_slot, text_slot), res in zip(slots, results):
                draw_frame(image_slot, text_slot, maze, res, frame_step, result_px)
            time.sleep(0.5 / speed)
        st.session_state.jump_to_end = True       # next run shows the final state
        st.rerun()
    st.caption("Tip: clicking any control while it plays stops the animation.")