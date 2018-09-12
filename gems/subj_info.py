import socket
import pickle
from os import path

import yaml
from psychopy import gui, data, core

from .config import DATA_DIR
from .inherited_instructions import load_ancestor_instructions


def get_subj_info(gui_yaml, check_exists=None, verify=None, save_order=False):
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


    Expected YAML data
    ------------------

        # contents of gui.yml
        ---
        1:
          name: subj_id
          prompt: Subject identifier
          default: GEMS100

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
        elif verify is not None and verify(subj_info):
            popup_error(verify(subj_info))
        else:
            with open(last_subj_info, 'wb') as f:
                pickle.dump(subj_info, f)
            break

    if save_order:
        subj_info['_order'] = ordered_names + fixed_fields
    return subj_info



def make_output_filepath(subj_info):
    return path.join(DATA_DIR, '%s.csv' % (subj_info['subj_id'], ))


def check_output_filepath(subj_info):
    return path.exists(make_output_filepath(subj_info))


def verify_subj_info(subj_info):
    try:
        generation = int(subj_info["generation"])
    except ValueError:
        return "Generation must be an integer"

    if generation < 1:
        return "Generation must be an integer greater than 1"

    ancestor_id = subj_info.get("inherit_from")
    if generation > 1:
        if not ancestor_id:
            return "If Generation > 1, ancestor id must be provided"

        try:
            load_ancestor_instructions(ancestor_id)
        except IOError:
            return "Ancestor instructions for '{}' not found".format(ancestor_id)


def convert_condition_vars(subj_info):
    new_subj_info = subj_info.copy()
    new_subj_info['filename'] = make_output_filepath(subj_info)
    new_subj_info['generation'] = int(subj_info['generation'])
    return new_subj_info


def popup_error(text):
	errorDlg = gui.Dlg(title="Error", pos=(200,400))
	errorDlg.addText('Error: '+text, color='Red')
	errorDlg.show()
