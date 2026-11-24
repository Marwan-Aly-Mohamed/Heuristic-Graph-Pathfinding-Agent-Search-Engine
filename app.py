"""Streamlit app - Stage 8: difficulty presets, editor, algorithms, playback, dashboard, export."""

import math
import time
from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates

from core.editor import TOOLS, handle_click
from core.maze import DIFFICULTY_LEVELS, DIFFICULTY_OPTIONS, MAX_SIZE, Maze
from core.metrics import build_metrics, compare_summary, display_rows
from core.pathfinding import ALGORITHMS, compare_algorithms, run_search
from core.result import SearchResult
from visualization.visualizer import FRONTIER, codes_to_image, frame_codes
from core.editor import TOOLS, handle_click
from core.exporter import build_export, to_csv, to_json

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


def export_files(maze, results, include_steps):
    """Build the CSV and JSON text ONCE per search (and per checkbox choice), then reuse it.
    Streamlit reruns the script on every click, so rebuilding a big JSON each time would be wasteful."""
    cache = st.session_state.setdefault("export_cache", {})
    key = (st.session_state.results_version, include_steps)
    if cache.get("key") != key:
        cache.clear()
        cache["key"] = key
        cache["csv"] = to_csv(maze, results)
        cache["json"] = to_json(build_export(maze, results, include_steps))
        cache["name"] = "pathfinding_results_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    return cache["csv"], cache["json"], cache["name"]


def render_export(maze, results):
    """Download buttons for the CSV (metrics) and JSON (full details and replay log)."""
    st.subheader("Export results")
    include_steps = st.checkbox(
        "Include the step-by-step replay log in the JSON file (makes the file bigger)",
        value=True, key="include_steps",
    )
    csv_text, json_text, base_name = export_files(maze, results, include_steps)
    c1, c2, _ = st.columns([1, 1, 2])
    c1.download_button("Download CSV (metrics)", csv_text, file_name=base_name + ".csv",
                       mime="text/csv", on_click="ignore", key="download_csv")
    c2.download_button("Download JSON (full log)", json_text, file_name=base_name + ".json",
                       mime="application/json", on_click="ignore", key="download_json")
    st.caption(f"CSV: {len(csv_text) / 1024:.1f} KB | JSON: {len(json_text) / 1024:.0f} KB")


# ---------- session state: memory that survives reruns ----------
if "maze" not in st.session_state:
    st.session_state.maze = Maze.random(20, 30, 0.25, seed=2)
if "last_click" not in st.session_state:
    st.session_state.last_click = None          # time stamp of the last click we used
if "results" not in st.session_state:
    st.session_state.results = None             # list of SearchResult (1 or 2)
    st.session_state.results_signature = None   # which maze those results belong to
    st.session_state.results_version = 0        # +1 for every new search (used by the export cache)

maze = st.session_state.maze


def store_results(results):
    """Remember results, the maze they belong to, and show the finished search."""
    st.session_state.results = results
    st.session_state.results_signature = maze.signature()
    st.session_state.results_version += 1
    st.session_state.step_slider = max(len(r.steps) for r in results)


# ---------- sidebar ----------
with st.sidebar:
    st.header("Maze settings")
    rows = st.slider("Rows", 5, MAX_SIZE, 20)
    cols = st.slider("Columns", 5, MAX_SIZE, 30)
    difficulty = st.selectbox(
    "Difficulty", DIFFICULTY_OPTIONS, index=1,
    help="Easy = 10% walls, Medium = 25%, Hard = 40%. Choose Custom to set your own density.",
    )
    custom_density = st.slider("Custom obstacle density", 0.0, 0.6, 0.25, 0.05,
                               disabled=(difficulty != "Custom"))
    density = DIFFICULTY_LEVELS.get(difficulty, custom_density)
    seed = st.number_input("Random seed", min_value=0, max_value=99999, value=2, step=1)
    ensure_path = st.checkbox(
        "Make sure a path exists", value=True,
        help="If the first maze has no route from start to goal, the next seeds are tried.",
    )

    if st.button("Generate random maze"):
        if ensure_path:
            new_maze, used_seed = Maze.random_solvable(rows, cols, density, int(seed))
        else:
            new_maze, used_seed = Maze.random(rows, cols, density, seed=int(seed)), int(seed)
        if new_maze is None:
            st.warning("Could not find a solvable maze with these settings. "
                       "Try a lower density, or turn off 'Make sure a path exists'.")
        else:
            st.session_state.maze = new_maze
            st.session_state.generated_info = f"Generated with {round(density * 100)}% walls, seed {used_seed}"
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

if st.session_state.get("generated_info"):
    st.caption(st.session_state.generated_info)

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
    render_export(maze, results)

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