from os import path

from .data import make_output_filepath
from .util import parse_pos_list


def verify_condition_vars(subj_info):
    try:
        parse_pos_list(subj_info['start_pos_list'])
    except Exception as err:
        print('Error parsing pos: %s' % err)
        return str(err)

    return False

def convert_condition_vars(subj_info):
    new_subj_info = subj_info.copy()
    new_subj_info['starting_positions'] = parse_pos_list(subj_info['start_pos_list'])
    new_subj_info['filename'] = make_output_filepath(subj_info)
    return new_subj_info
