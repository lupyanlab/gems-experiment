from itertools import product


def pos_to_str(pos):
    x, y = pos
    return '{x}-{y}'.format(x=x, y=y)

def pos_list_to_str(pos_list):
    return ';'.join([pos_to_str(pos) for pos in pos_list])

def parse_pos(str_pos):
    return tuple(map(int, str_pos.split('-')))

def parse_pos_list(str_pos_list):
    return [parse_pos(str_pos) for str_pos in str_pos_list.split(';')]

def get_pos_list_from_ix(pos_list_ix):
    pos_lists = [pos_list_str.strip() for pos_list_str in open('pos-lists.txt')]
    assert pos_list_ix < len(pos_lists), "pos_list_ix is too big! Max is %s" % (len(pos_lists)-1)
    return parse_pos_list(pos_lists[pos_list_ix])

def create_grid(n_rows, n_cols):
    """Create all row, col grid positions.

    Grid positions are given as positive indices starting at 0.
    Rows range from 0 to (n_rows-1).
    Columns range from 0 to (n_cols-1).

    Grid positions are [(0, 0), (0, 1), ..., (n_rows-1, n_cols-1)]
    """
    return product(range(n_rows), range(n_cols))
