import pytest

from gems import create_stim_positions

def test_create_single_position():
    positions = create_stim_positions(n_rows=1, n_cols=1, win_size=(100, 100))
    assert list(positions) == [(-50, -50)]

def test_create_four_corner_positions():
    positions = create_stim_positions(n_rows=2, n_cols=2, win_size=(100, 100))
    assert list(positions) == [(-50, -50), (-50, 50), (50, -50), (50, 50)]
