"""Draws the maze and replays the search using the `steps` log.

Idea: every cell gets a small integer CODE (empty, wall, explored, ...).
  frame_codes()    -> builds the grid of codes for a chosen step
  codes_to_image() -> turns codes into a colored picture (numpy array)
  save_gif()       -> animation of the whole search
  make_figure()    -> matplotlib figure with titles + legend (for PNG export)
"""

import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure
from matplotlib.patches import Patch
from PIL import Image

EMPTY, WALL, EXPLORED, FRONTIER, PATH, START, GOAL = range(7)

COLORS = {
    EMPTY: "#FFFFFF",
    WALL: "#2B2B2B",
    EXPLORED: "#B3E5FC",   # light blue  - already expanded
    FRONTIER: "#FFB74D",   # orange      - waiting in the queue
    PATH: "#43A047",       # green       - final path
    START: "#1565C0",      # dark blue
    GOAL: "#E53935",       # red
}
LABELS = {
    EMPTY: "Empty", WALL: "Wall", EXPLORED: "Explored", FRONTIER: "Waiting",
    PATH: "Final path", START: "Start", GOAL: "Goal",
}


def _hex_to_rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


PALETTE = np.array([_hex_to_rgb(COLORS[i]) for i in range(7)], dtype=np.uint8)


def frame_codes(maze, result, step=None, show_path=True):
    """Grid of codes showing the search after `step` expansions.
    step=None means 'the whole search'. The path appears only at the very end."""
    total = len(result.steps)
    step = total if step is None else max(0, min(step, total))

    codes = np.where(maze.grid == 1, WALL, EMPTY).astype(np.int8)

    expanded = set()
    waiting = {maze.start} if maze.is_walkable(maze.start) else set()
    for node, pushed in result.steps[:step]:
        expanded.add(node)
        waiting.update(pushed)
    waiting -= expanded

    for r, c in expanded:
        codes[r, c] = EXPLORED
    for r, c in waiting:
        codes[r, c] = FRONTIER

    if show_path and result.found and step == total:
        for r, c in result.path:
            codes[r, c] = PATH

    # Start and goal are painted last so they are always visible
    if maze.in_bounds(maze.start):
        codes[maze.start] = START
    if maze.in_bounds(maze.goal):
        codes[maze.goal] = GOAL
    return codes


def codes_to_image(codes, cell_px=12):
    """RGB picture (height x width x 3, uint8). Each cell becomes cell_px x cell_px."""
    img = PALETTE[codes]
    img = np.repeat(np.repeat(img, cell_px, axis=0), cell_px, axis=1)
    if cell_px >= 6:                          # thin light-grey grid lines
        img[::cell_px, :, :] = 221
        img[:, ::cell_px, :] = 221
    return img


def save_gif(maze, result, path, cell_px=10, max_frames=60, frame_ms=80, final_hold_ms=1500):
    """Animated GIF of the search. Long searches are sampled to <= max_frames."""
    total = len(result.steps)
    wanted = min(max_frames, total + 1)
    indices = sorted(set(np.linspace(0, total, num=wanted).astype(int).tolist()))

    frames = [Image.fromarray(codes_to_image(frame_codes(maze, result, i), cell_px))
              for i in indices]
    durations = [frame_ms] * len(frames)
    durations[-1] = final_hold_ms             # pause on the final path
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0)
    return len(frames)


def make_figure(maze, results, step=None):
    """Matplotlib figure: one panel per result, with a title and a color legend.
    Pass 1 result for a single run, or 2 for a side-by-side comparison."""
    if not isinstance(results, (list, tuple)):
        results = [results]

    cmap = ListedColormap([COLORS[i] for i in range(7)])
    panel_w = 5.5
    panel_h = panel_w * maze.rows / maze.cols       # follow the maze's shape
    fig = Figure(figsize=(max(panel_w * len(results), 8.5), panel_h + 1.6))
    axes = fig.subplots(1, len(results), squeeze=False)[0]

    for ax, res in zip(axes, results):
        codes = frame_codes(maze, res, step)
        ax.imshow(codes, cmap=cmap, vmin=0, vmax=6, interpolation="nearest")
        total = len(res.steps)
        if step is not None and step < total:        # a snapshot in the middle
            info = f"step {max(step, 0)} of {total} expansions"
        elif res.found:
            info = f"path = {res.path_length} moves, expanded = {res.expanded_nodes}"
        else:
            info = f"NO PATH, expanded = {res.expanded_nodes}"
        ax.set_title(f"{res.algorithm}\n{info}", fontsize=11)
        ax.set_xticks([])
        ax.set_yticks([])

    handles = [Patch(facecolor=COLORS[i], edgecolor="#888888", label=LABELS[i]) for i in range(7)]
    fig.legend(handles=handles, loc="lower center", ncol=7, fontsize=9, frameon=False)
    fig.subplots_adjust(bottom=0.14, top=0.84, wspace=0.08)
    return fig