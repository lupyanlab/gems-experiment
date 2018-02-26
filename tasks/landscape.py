import sys

from os import path, mkdir
from itertools import product
from invoke import task

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import gems


@task
def data(ctx, name, move_to_r_pkg=False):
    """Save the landscape to a tidy csv.

    Examples:

        $ inv landscape.data SimpleHill

    """
    landscapes = get_landscapes_from_name(name)

    if move_to_r_pkg:
        landscapes_dir = '../data/data-raw/landscapes'
        if not path.isdir(landscapes_dir):
            mkdir(landscapes_dir)

    for name, landscape in landscapes.items():
        if move_to_r_pkg:
            output = path.join(landscapes_dir, '{}.csv'.format(name))
        else:
            output = path.join(gems.config.LANDSCAPE_FILES, '{}.csv'.format(name))

        landscape.export(output)


@task
def gabors(ctx, name, output=None, move_to_r_pkg=False, open_after=False):
    """Draw gabors sampled from the landscape.

    Examples:

        $ inv landscape.draw SimpleHill

    """
    from psychopy import visual
    from numpy import linspace

    if move_to_r_pkg:
        gabors_dir = '../data/inst/extdata'
        if not path.isdir(gabors_dir):
            mkdir(gabors_dir)

    win = visual.Window(size=(800, 800), units='pix', color=(0.6, 0.6, 0.6))

    grid_size = 10
    positions = linspace(0, 100, grid_size, endpoint=False, dtype='int')
    grid_positions = list(product(positions, positions))

    gabor_size = 60
    positions = linspace(0, 100, grid_size, endpoint=False, dtype='int')
    grid_positions = list(product(positions, positions))
    stim_positions = gems.create_grid_positions(n_rows=grid_size, n_cols=grid_size,
                                           win_size=win.size,
                                           stim_size=gabor_size)

    output_dir = gabors_dir if move_to_r_pkg else gems.config.GABORS_DIR

    landscapes = get_landscapes_from_name(name)
    for name, landscape in landscapes.items():
        landscape.grating_stim_kwargs.update({'win': win, 'size': gabor_size})
        gabors = landscape.get_grid_of_grating_stims(grid_positions)

        for (grid_pos, stim_pos) in zip(grid_positions, stim_positions):
            gabor = gabors[grid_pos]
            gabor.pos = stim_pos
            gabor.draw()

            label = visual.TextStim(win, '%s' % (grid_pos, ), pos=(stim_pos[0], stim_pos[1]+gabor_size/2), alignVert='bottom')
            label.draw()

        win.flip()
        win.getMovieFrame()

        output = path.join(output_dir, '{}Gems.png'.format(name))
        win.saveMovieFrames(output)

        if open_after:
            ctx.run('open %s' % (output, ), echo=True)


@task
def draw(ctx, name, open_after=False):
    """Draw the landscape as a 3D plot."""
    landscapes = get_landscapes_from_name(name)
    for name, landscape in landscapes.items():
        data = landscape.to_tidy_data()
        grid = data[['x', 'y', 'score']].pivot('x', 'y', 'score')

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.contour3D(range(100), range(100), grid, 50)
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('score')

        output = path.join(gems.config.LANDSCAPE_FILES, '{}Scores.png'.format(name))
        fig.savefig(output)

        if open_after:
            ctx.run('open {}'.format(output), echo=True)


@task
def radius(ctx, grid_pos='10-10', sight_radius=8):
    """Draw gabors in a given search radius."""
    grid_positions = gems.create_grid(sight_radius, sight_radius, centroid=pos_from_str(grid_pos))


def get_landscapes_from_name(name):
    if name == 'all':
        names = ['SimpleHill', 'OrientationBias', 'SpatialFrequencyBias', 'ReverseOrientation', 'ReverseSpatialFrequency', 'ReverseBoth']
    else:
        names = [name, ]

    landscapes = {}
    for name in names:
        Landscape = getattr(gems.landscape, name, None)
        if Landscape is None:
            msg = "Landscape '{}' not found."
            print(msg.format(name))
            sys.exit(1)
        landscapes[name] = Landscape()

    return landscapes
