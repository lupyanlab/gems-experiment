from os import path
from .config import DATA_DIR

data_columns = [
    'subj_id', 'date', 'computer', 'experimenter',
    'instructions', 'sight_radius', 'n_gabors',
    'landscape_ix', 'landscape_name', 'starting_pos', 'trial',
    'feedback', 'pos', 'stims',
    'selected', 'rt', 'score', 'delta', 'total',
]

def make_output_filepath(subj_info):
    return path.join(DATA_DIR, '%s.csv' % (subj_info['subj_id'], ))

def check_output_filepath(subj_info):
    return path.exists(make_output_filepath(subj_info))
