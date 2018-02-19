import sys
import subprocess
from os import path, mkdir
from itertools import product
from numpy import linspace

from invoke import task

import gems
from gems import Experiment
from gems.display import create_grid_positions


@task
def show_texts(ctx, instructions_condition='orientation'):
    """Show the instructions for the experiment."""
    Experiment.win_size = (600 * 2, 400 * 2)
    experiment = Experiment(instructions_condition=instructions_condition)
    experiment.show_welcome()
    experiment.show_training()
    experiment.show_test()
    # experiment.show_break()
    # experiment.show_end()
    experiment.quit()


@task
def gui(ctx):
    """Open the subject info GUI and print the results."""
    experiment = Experiment.from_gui('gui.yml')
    print(experiment.condition_vars)


@task
def run_trial(ctx):
    """Run a single trial."""
    Experiment.win_size = (600 * 2, 400 * 2)
    experiment = Experiment()
    trial_data = experiment.run_trial()
    print(trial_data)
    experiment.quit()


@task
def run_test_trials(ctx, n_test_trials=1):
    """Run test trials."""
    Experiment.win_size = (600 * 2, 400 * 2)
    experiment = Experiment(subj_id='pierce')
    experiment.run_test_trials(n_test_trials)


@task
def run_training_trials(ctx, n_training_trials=1):
    """Run training trials."""
    Experiment.win_size = (600 * 2, 400 * 2)
    experiment = Experiment(subj_id='pierce')
    experiment.run_training_trials(n_training_trials)
    experiment.quit()


@task
def print_landscape(ctx, name, output=None, move_to_r_pkg=False):
    """Print the landscape to a tidy csv.

    Examples:
    $ inv print-landscape SimpleHill

    """
    Landscape = getattr(gems.landscape, name, None)
    if Landscape is None:
        msg = "Landscape '{}' not found."
        print(msg.format(name))
        sys.exit(1)

    if output is None:
        output = path.join(gems.config.LANDSCAPE_FILES, '{}.csv'.format(name))

    if move_to_r_pkg:
        landscapes_dir = '../data/data-raw/landscapes'
        if not path.isdir(landscapes_dir):
            mkdir(landscapes_dir)
        output = path.join(landscapes_dir, '{}.csv'.format(name))

    landscape = Landscape()
    landscape.export(output)


@task
def draw_landscape(ctx, name, output=None, open_after=False):
    """Draw the landscape as a 3D plot."""
    if output is None:
        output = path.join(gems.config.LANDSCAPE_FILES, '{}.pdf'.format(name))
    R_command = 'Rscript -e "gems::save_landscape({name!r}, {output!r})"'
    ctx.run(R_command.format(name=name, output=output), echo=True)
    if open_after:
        ctx.run('open %s' % (output, ), echo=True)


@task
def draw_gabors(ctx, grid_size=10, win_size=None, output='landscape.png',
                open_after=False):
    """Draw gabors sampled from the landscape.

    Examples:
    $ inv draw-gabors -w 800 -p
    """
    from psychopy import visual

    if win_size is None:
        fullscr = True
        size = (1, 1)  # Ignored when full screen
    else:
        fullscr = False
        size = map(int, win_size.split(','))
        if len(size) == 1:
            size = (size, size)

    win = visual.Window(size=size, units='pix', color=(0.6, 0.6, 0.6),
                        fullscr=fullscr)

    positions = linspace(0, 100, grid_size, endpoint=False, dtype='int')
    grid_positions = list(product(positions, positions))

    gabor_size = 60

    landscape = SimpleHill()
    landscape.grating_stim_kwargs = {'win': win, 'size': gabor_size}

    # Get gabors for each point in the grid
    positions = linspace(0, 100, grid_size, endpoint=False, dtype='int')
    grid_positions = list(product(positions, positions))
    gabors = landscape.get_gabors(grid_positions)

    stim_positions = create_grid_positions(n_rows=grid_size, n_cols=grid_size,
                                           win_size=win.size,
                                           stim_size=gabor_size)

    for (grid_pos, stim_pos) in zip(grid_positions, stim_positions):
        gabor = gabors[grid_pos]
        gabor.pos = stim_pos
        gabor.draw()

        label = visual.TextStim(win, '%s' % (grid_pos, ), pos=(stim_pos[0], stim_pos[1]+gabor_size/2), alignVert='bottom')
        label.draw()

    win.flip()
    win.getMovieFrame()
    win.saveMovieFrames(output)
    win.close()

    if open_after:
        ctx.run('open %s' % (output, ), echo=True)


@task
def draw_search_radius(ctx, grid_pos='10-10', search_radius=8):
    grid_positions = create_grid(search_radius, search_radius, centroid=pos_from_str(grid_pos))
