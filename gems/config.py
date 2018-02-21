from os import path, mkdir

pkg_root = path.dirname(path.abspath(__file__))
EXP_ROOT = path.dirname(pkg_root)
DATA_DIR = path.join(EXP_ROOT, 'data')
LANDSCAPE_FILES = path.join(pkg_root, 'landscapes')
GABORS_DIR = path.join(pkg_root, 'gabors')

for expected_dir in [DATA_DIR, LANDSCAPE_FILES, GABORS_DIR]:
    if not path.isdir(expected_dir):
        mkdir(expected_dir)
