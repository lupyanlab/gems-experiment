from os import path, mkdir

PKG_ROOT = path.dirname(path.abspath(__file__))
EXP_ROOT = path.dirname(PKG_ROOT)
DATA_DIR = path.join(EXP_ROOT, 'data')
LANDSCAPE_FILES = path.join(PKG_ROOT, 'landscapes')

if not path.isdir(DATA_DIR):
    mkdir(DATA_DIR)

if not path.isdir(LANDSCAPE_FILES):
    mkdir(LANDSCAPE_FILES)
