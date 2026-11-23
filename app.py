"""Streamlit app - Step 7.3: maze editor + choose an algorithm + run it."""

import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates

from core.editor import TOOLS, handle_click
from core.maze import MAX_SIZE, Maze
from core.pathfinding import ALGORITHMS, compare_algorithms, run_search
from core.result import SearchResult
from visualization.visualizer import codes_to_image, frame_codes

st.set_page_config(page_title="Pathfinding Agent", layout="wide")
st.title("Heuristic Graph Pathfinding Agent Search Engine")

# ---------- session state: memory that survives reruns ----------
if "maze" not in st.session_state:
    st.session_state.maze = Maze.random(20, 30, 0.25, seed=2)
if "last_click" not in st.session_state:
    st.session_state.last_click = None          # time stamp of the last click we used
if "results" not in st.session_state:
    st.session_state.results = None             # list of SearchResult (1 or 2)
    st.session_state.results_signature = None   # which maze those results belong to

maze = st.session_state.maze

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
        st.session_state.results = [run_search(maze, algorithm, repeats)]
        st.session_state.results_signature = maze.signature()

    if st.button("Compare both algorithms"):
        results, _ = compare_algorithms(maze, repeats)
        st.session_state.results = results
        st.session_state.results_signature = maze.signature()

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
    result_px = max(4, min(16, 600 // maze.cols))
    panels = st.columns(len(results))
    for panel, res in zip(panels, results):
        with panel:
            st.markdown(f"**{res.algorithm}**")
            st.image(codes_to_image(frame_codes(maze, res), result_px), width="stretch")
            if res.found:
                st.success(f"Path found: {res.path_length} moves, {res.expanded_nodes} nodes expanded")
            else:
                st.error(f"No path found: {res.error} ({res.expanded_nodes} nodes expanded)")