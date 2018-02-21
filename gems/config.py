from os import path, mkdir

pkg_root = path.dirname(path.abspath(__file__))
EXP_ROOT = path.dirname(pkg_root)
DATA_DIR = path.join(EXP_ROOT, 'data')
LANDSCAPE_FILES = path.join(pkg_root, 'landscapes')

if not path.isdir(DATA_DIR):
    mkdir(DATA_DIR)

if not path.isdir(LANDSCAPE_FILES):
    mkdir(LANDSCAPE_FILES)
