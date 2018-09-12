from os import path
from .config import INSTRUCTIONS_DIR


def load_ancestor_instructions(ancestor_id):
    return open(path.join(INSTRUCTIONS_DIR, "{}.txt".format(ancestor_id))).read()
