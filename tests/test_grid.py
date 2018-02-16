from gems.util import create_grid

def test_create_grid():
    grid = create_grid(1, 1)
    assert list(grid) == [(0, 0)]
