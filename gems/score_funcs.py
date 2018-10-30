import math

def simple_hill(grid_pos, normalize=True):
    """Get the height of a simple hill with peak at (50, 50)."""
    x, y = grid_pos
    score = (-x**2) - (y**2) + (100*x) + (100*y)
    if normalize:
        max_height = 5000.0
        score = int((score/max_height) * 100)

    return score

def orientation_bias(grid_pos, normalize=True):
    x, _ = grid_pos
    score = (-x**2) + (100*x)
    if normalize:
        max_height = 2500.0
        score = int((score/max_height) * 100)

    return score

def spatial_frequency_bias(grid_pos, normalize=True):
    _, y = grid_pos
    score = (-y**2) + (100*y)
    if normalize:
        max_height = 2500.0
        score = int((score/max_height) * 100)

    return score
