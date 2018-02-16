from os import path

from .data import output_filepath_from_subj_info
from .util import parse_pos

def check_output_filepath_exists(subj_info):
    return path.exists(output_filepath_from_subj_info(subj_info))

def verify_subj_info_strings(subj_info):
    try:
        parse_pos(subj_info['training_pos'])
        parse_pos(subj_info['starting_pos'])
    except Exception as err:
        print('Error parsing pos: %s' % err)
        return str(err)

    return False

def parse_subj_info_strings(subj_info):
    new_subj_info = subj_info.copy()
    new_subj_info['search_radius'] = int(subj_info['search_radius'])
    new_subj_info['training_pos'] = parse_pos(subj_info['training_pos'])
    new_subj_info['starting_pos'] = parse_pos(subj_info['starting_pos'])
    return new_subj_info
