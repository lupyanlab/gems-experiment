from os import path

from .data import make_output_filepath
from .util import get_pos_list_from_ix


def verify_condition_vars(subj_info):
    try:
        get_pos_list_from_ix(subj_info['start_pos_list_ix'])
    except Exception as err:
        print('Unable to verify condition variables: %s' % err)
        return str(err)

    return False

def convert_condition_vars(subj_info):
    new_subj_info = subj_info.copy()
    new_subj_info['starting_positions'] = \
        get_pos_list_from_ix(subj_info['start_pos_list_ix'])
    new_subj_info['filename'] = make_output_filepath(subj_info)
    return new_subj_info
