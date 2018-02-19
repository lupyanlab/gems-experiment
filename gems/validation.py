from os import path

from .data import output_filepath_from_subj_info
from .util import parse_pos_list

def check_output_filepath_exists(subj_info):
    return path.exists(output_filepath_from_subj_info(subj_info))

def verify_subj_info_strings(subj_info):
    try:
        parse_pos_list(subj_info['start_pos_list'])
    except Exception as err:
        print('Error parsing pos: %s' % err)
        return str(err)

    return False

def parse_subj_info_strings(subj_info):
    new_subj_info = subj_info.copy()
    new_subj_info['starting_positions'] = parse_pos_list(subj_info['start_pos_list'])
    return new_subj_info
