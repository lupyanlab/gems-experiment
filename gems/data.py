from os import path
from .config import DATA_DIR

DATA_COLUMNS = [
    'subj_id', 'date', 'computer', 'experimenter',
    'instructions', 'sight_radius', 'n_search_items',
    'landscape_ix', 'landscape_name', 'starting_pos', 'trial',
    'feedback', 'pos', 'stims',
    'selected', 'rt', 'score', 'delta', 'total',
]

def output_filepath_from_subj_info(subj_info):
    return path.join(DATA_DIR, '%s.csv' % (subj_info['subj_id'], ))
