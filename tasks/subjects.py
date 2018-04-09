import itertools
from invoke import task
import pandas

from tasks.googledrive import connect_google_sheets


@task
def update_subj_info(ctx):
    """Update the subj info sheet with generation 2 starting positions.

    Assumes the pos lists have already been exported via:

        experiment/$ inv exp.write-pos-lists  # creates "pos-lists.txt"
    """
    pos_lists = 'pos-lists.txt'
    pos_list_strs = [pos_list_str.strip() for pos_list_str in open(pos_lists)]
    pos_list_ixs = range(1, len(pos_list_strs))

    instructions_conditions = ['orientation', 'spatial_frequency']

    subj_info = pandas.DataFrame.from_records(
        list(itertools.product(pos_list_ixs, instructions_conditions)),
        columns=['starting_pos_list_ix', 'instructions_condition']
    ).sort_values(['starting_pos_list_ix', 'instructions_condition'])

    gc = connect_google_sheets()
    wb = gc.open('gems-subj-info')
    ws = wb.worksheet('generation2')

    cells = ws.range('D2:D{}'.format(2+len(subj_info.instructions_condition)))
    for cell, value in zip(cells, subj_info.instructions_condition):
        cell.value = value
    ws.update_cells(cells)

    cells = ws.range('E2:E{}'.format(2+len(subj_info.starting_pos_list_ix)))
    for cell, value in zip(cells, subj_info.starting_pos_list_ix):
        cell.value = value
    ws.update_cells(cells)
