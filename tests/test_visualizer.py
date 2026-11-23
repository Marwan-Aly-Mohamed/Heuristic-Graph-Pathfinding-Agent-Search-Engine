import numpy as np
import pytest
from PIL import Image

from core.maze import Maze
from core.pathfinding import compare_algorithms, run_search
from visualization.visualizer import (EMPTY, EXPLORED, FRONTIER, GOAL, PATH, START, WALL,
                                      codes_to_image, frame_codes, make_figure, save_gif)


def solved(name="A*", seed=3):
    m = Maze.random(20, 30, 0.2, seed=seed)
    r = run_search(m, name)
    assert r.found
    return m, r


def test_step_zero_shows_only_maze_start_goal_and_waiting_start():
    m, r = solved()
    codes = frame_codes(m, r, step=0)
    assert codes[m.start] == START and codes[m.goal] == GOAL
    assert not (codes == EXPLORED).any()
    assert not (codes == PATH).any()


def test_walls_never_change():
    m, r = solved()
    for step in (0, 5, len(r.steps) // 2, len(r.steps)):
        codes = frame_codes(m, r, step)
        assert ((codes == WALL) == (m.grid == 1)).all()


def test_explored_cells_match_the_steps_log():
    m, r = solved("Dijkstra")
    k = len(r.steps) // 2
    codes = frame_codes(m, r, k)
    expanded = {node for node, _ in r.steps[:k]}
    for cell in expanded:
        assert codes[cell] in (EXPLORED, START, GOAL)
    assert (codes == EXPLORED).sum() >= len(expanded) - 2   # minus start/goal overlays


def test_frontier_never_overlaps_explored_and_is_walkable():
    m, r = solved()
    for step in range(0, len(r.steps) + 1, 3):
        codes = frame_codes(m, r, step)
        for rr, cc in zip(*np.where(codes == FRONTIER)):
            assert m.is_walkable((rr, cc))


def test_path_only_appears_at_the_end():
    m, r = solved()
    assert not (frame_codes(m, r, len(r.steps) - 1) == PATH).any()
    final = frame_codes(m, r)
    inner = r.path[1:-1]                                   # exclude start/goal
    assert all(final[cell] == PATH for cell in inner)
    assert (final == PATH).sum() == len(inner)


def test_no_path_means_no_green_cells():
    m = Maze(8, 8)
    for row in range(8):
        m.add_wall((row, 4))
    r = run_search(m, "A*")
    assert not r.found
    assert not (frame_codes(m, r) == PATH).any()


def test_invalid_start_does_not_crash():
    m = Maze(5, 5)
    m.start = (9, 9)
    r = run_search(m, "A*")
    codes = frame_codes(m, r)
    assert codes.shape == (5, 5)


def test_step_is_clamped():
    m, r = solved()
    assert (frame_codes(m, r, -10) == frame_codes(m, r, 0)).all()
    assert (frame_codes(m, r, 10**9) == frame_codes(m, r)).all()


def test_image_shape_and_type():
    m, r = solved()
    img = codes_to_image(frame_codes(m, r), cell_px=8)
    assert img.shape == (m.rows * 8, m.cols * 8, 3)
    assert img.dtype == np.uint8


def test_gif_is_created_and_has_many_frames(tmp_path):
    m, r = solved()
    path = tmp_path / "search.gif"
    n = save_gif(m, r, str(path), cell_px=6, max_frames=30)
    assert path.exists() and path.stat().st_size > 0
    assert Image.open(path).n_frames == n and n > 1


def test_gif_handles_zero_step_result(tmp_path):
    m = Maze(5, 5)
    m.start = (9, 9)
    r = run_search(m, "A*")
    save_gif(m, r, str(tmp_path / "x.gif"))


def test_figure_single_and_comparison_save_as_png(tmp_path):
    m = Maze.random(20, 30, 0.2, seed=3)
    results, _ = compare_algorithms(m, repeats=1)
    for res_list, name in ((results[0], "one.png"), (results, "two.png")):
        fig = make_figure(m, res_list)
        out = tmp_path / name
        fig.savefig(out, dpi=80)
        assert out.exists() and out.stat().st_size > 1000


def test_midway_figure_title_shows_progress_not_final_stats():
    m, r = solved("Dijkstra")
    half = len(r.steps) // 2
    fig = make_figure(m, r, step=half)
    title = fig.axes[0].get_title()
    assert f"step {half} of {len(r.steps)}" in title
    assert "path =" not in title
    final_title = make_figure(m, r).axes[0].get_title()
    assert "path =" in final_title