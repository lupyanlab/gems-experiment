from itertools import product
from numpy import linspace

def create_stim_positions(n_rows, n_cols, win_size, stim_size=0):
    win_width, win_height = win_size
    win_left, win_right = -win_width/2, win_width/2
    win_bottom, win_top = -win_height/2, win_height/2

    # Sample row and column positions with stim sized buffer
    x_positions = linspace(win_left+stim_size, win_right-stim_size, num=n_cols, dtype='int')
    y_positions = linspace(win_bottom+stim_size, win_top-stim_size, num=n_rows, dtype='int')

    return list(product(x_positions, y_positions))
