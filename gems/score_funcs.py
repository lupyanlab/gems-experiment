
def simple_hill(grid_pos, normalize=True):
    """Get the height of a simple hill with peak at (50, 50)."""
    x, y = grid_pos
    score = (-x**2) - (y**2) + (100*x) + (100*y)
    if normalize:
        max_height = 5000.0
        score = int((score/max_height) * 100)

    return score
