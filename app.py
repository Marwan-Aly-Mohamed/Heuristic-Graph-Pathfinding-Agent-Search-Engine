"""Streamlit app - Step 7.2: maze editor (click on the picture to edit the maze)."""

import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates

from core.editor import TOOLS, handle_click
from core.maze import MAX_SIZE, Maze
from core.result import SearchResult
from visualization.visualizer import codes_to_image, frame_codes

st.set_page_config(page_title="Pathfinding Agent", layout="wide")
st.title("Heuristic Graph Pathfinding Agent Search Engine")

# ---------- session state: memory that survives reruns ----------
if "maze" not in st.session_state:
    st.session_state.maze = Maze.random(20, 30, 0.25, seed=2)
if "last_click" not in st.session_state:
    st.session_state.last_click = None          # time stamp of the last click we used

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

# ---------- main area: the clickable maze ----------
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