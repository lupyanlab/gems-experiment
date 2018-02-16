from os import path
from .config import DATA_DIR

DATA_COLUMNS = [
    'subj_id', 'date', 'computer', 'experimenter',
    'instructions', 'search_radius', 'n_search_items',
    'quarry', 'starting_pos', 'feedback', 'trial',
    'pos', 'stims', 'selected', 'rt', 'score', 'total',
]

def output_filepath_from_subj_info(subj_info):
    return path.join(DATA_DIR, '%s.csv' % (subj_info['subj_id'], ))
