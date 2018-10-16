from os import path, mkdir

pkg_root = path.dirname(path.abspath(__file__))
EXP_ROOT = path.dirname(pkg_root)
DATA_DIR = path.join(EXP_ROOT, 'data')
INSTRUCTIONS_DIR = path.join(DATA_DIR, 'instructions')
LANDSCAPE_FILES = path.join(pkg_root, 'landscapes')
GABORS_DIR = path.join(pkg_root, 'gabors')

for expected_dir in [DATA_DIR, INSTRUCTIONS_DIR, LANDSCAPE_FILES, GABORS_DIR]:
    if not path.isdir(expected_dir):
        mkdir(expected_dir)

data_columns = [
    'subj_id', 'date', 'computer', 'experimenter', 'version',
    'generation', 'inherit_from',
    'sight_radius', 'n_gabors',
    'block_ix', 'landscape_name', 'starting_pos', 'starting_score',
    'trial', 'pos', 'stims',
    'selected', 'rt', 'score', 'delta',
    'exp_time'
]

simulation_data_columns = [
    'simulation_type',
    'subj_id',
    'sight_radius', 'n_gabors',
    'block_ix', 'landscape_name', 'starting_pos', 'starting_score',
    'trial', 'pos', 'stims',
    'selected', 'score', 'delta'
]
