from os import path
from .config import DATA_DIR

data_columns = [
    'subj_id', 'date', 'computer', 'experimenter',
    'instructions', 'sight_radius', 'n_gabors', 'start_pos_list_ix', 'start_pos_list',
    'landscape_ix', 'landscape_name', 'starting_pos', 'starting_score', 'trial',
    'feedback', 'pos', 'stims',
    'selected', 'rt', 'score', 'delta',
    'exp_time'
]

def make_output_filepath(subj_info):
    return path.join(DATA_DIR, '%s.csv' % (subj_info['subj_id'], ))

def check_output_filepath(subj_info):
    return path.exists(make_output_filepath(subj_info))
