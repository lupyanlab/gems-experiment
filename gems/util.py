import socket
import pickle
from itertools import product

import yaml

from psychopy import gui, data, core

def pos_to_str(pos):
    x, y = pos
    return '{x}-{y}'.format(x=x, y=y)

def pos_list_to_str(pos_list):
    return ';'.join([pos_to_str(pos) for pos in pos_list])

def parse_pos(str_pos):
    return map(int, str_pos.split(','))

def parse_pos_list(str_pos_list):
    return [parse_pos(str_pos) for str_pos in str_pos_list.split(';')]

def create_grid(n_rows, n_cols):
    """Create all row, col grid positions.

    Grid positions are given as positive indices starting at 0.
    Rows range from 0 to (n_rows-1).
    Columns range from 0 to (n_cols-1).

    Grid positions are [(0, 0), (0, 1), ..., (n_rows-1, n_cols-1)]
    """
    return product(range(n_rows), range(n_cols))


def get_subj_info(gui_yaml, check_exists, verify=lambda subj_info: True, save_order=True):
    """Create a psychopy.gui from a yaml config file.

    The first time the experiment is run, a pickle of that subject's settings
    is saved. On subsequent runs, the experiment tries to prepopulate the
    settings with those of the previous subject.

    Parameters
    ----------
    gui_yaml: str, Path to config file in yaml format.
    check_exists: function, Computes a data file path from the gui data, and
        checks for its existence. If the file exists, an error is displayed.
    verify: function, Evaluates the inputs from the gui. If an input doesn't
        verify, an error is displayed.
    save_order: bool, Should the key order be saved in "_order"? Defaults to
        True.

    Returns
    -------
    dict, with key order saved in "_order", if specified.
    """
    with open(gui_yaml, 'r') as f:
        gui_info = yaml.load(f)

    ordered_fields = [field for _, field in sorted(gui_info.items())]

    # Determine order and tips
    ordered_names = [field['name'] for field in ordered_fields]
    field_tips = {field['name']: field['prompt'] for field in ordered_fields}

    # Load the last participant's options or use the defaults
    last_subj_info = gui_yaml + '.pickle'
    try:
        with open(last_subj_info, 'rb') as f:
            gui_data = pickle.load(f)

        for yaml_name in ordered_names:
            if yaml_name not in gui_data:
                # Invalid pickle
                print('Invalid pickle')
                raise AssertionError
    except (IOError, ValueError, AssertionError) as e:
        print('caught error: %s' % e)
        gui_data = {field['name']: field['default'] for field in ordered_fields}
    else:
        # Successfully loaded previous participant's gui data.
        # Now to repopulate the values with options.
        for field in ordered_fields:
            options = field['default']
            if isinstance(options, list) and len(options) > 1:
                selected = gui_data[field['name']]
                options.pop(options.index(selected))
                options.insert(0, selected)
                gui_data[field['name']] = options

    # Set fixed fields
    gui_data['date'] = data.getDateStr()
    gui_data['computer'] = socket.gethostname()
    fixed_fields = ['date', 'computer']

    while True:
        # Bring up the dialogue
        dlg = gui.DlgFromDict(gui_data, order=ordered_names,
                              fixed=fixed_fields, tip=field_tips)

        if not dlg.OK:
            core.quit()

        subj_info = dict(gui_data)

        if check_exists(subj_info):
            popup_error('That subj_id already exists.')
        else:
            input_error = verify(subj_info)
            if input_error:
                popup_error(input_error)
            else:
                with open(last_subj_info, 'w') as f:
                    pickle.dump(subj_info, f)
                break

    if save_order:
        subj_info['_order'] = ordered_names + fixed_fields
    return subj_info

def popup_error(text):
	errorDlg = gui.Dlg(title="Error", pos=(200,400))
	errorDlg.addText('Error: '+text, color='Red')
	errorDlg.show()
