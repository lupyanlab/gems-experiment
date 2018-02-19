from os import path, mkdir
from itertools import product
from invoke import task
import gems


@task
def data(ctx, name, output=None, move_to_r_pkg=False):
    """Save the landscape to a tidy csv.

    Examples:

        $ inv landscape.data SimpleHill

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
def draw(ctx, name, output=None, open_after=False):
    """Draw the landscape as a 3D plot."""
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D

    Landscape = getattr(gems.landscape, name, None)
    if Landscape is None:
        msg = "Landscape '{}' not found."
        print(msg.format(name))
        sys.exit(1)

    if output is None:
        output = path.join(gems.config.LANDSCAPE_FILES, '{}.pdf'.format(name))

    landscape = Landscape()
    data = landscape.to_tidy_data()
    grid = data[['x', 'y', 'score']].pivot('x', 'y', 'score')

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.contour3D(range(100), range(100), grid, 50)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('score')
    fig.savefig(output)

    if open_after:
        ctx.run('open {}'.format(output), echo=True)


@task
def gabors(ctx, grid_size=10, win_size=None, output='landscape.png',
           open_after=False):
    """Draw gabors sampled from the landscape.

    Examples:
    $ inv draw-gabors -w 800 -p
    """
    from psychopy import visual
    from numpy import linspace

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

    landscape = gems.SimpleHill()
    landscape.grating_stim_kwargs = {'win': win, 'size': gabor_size}

    # Get gabors for each point in the grid
    positions = linspace(0, 100, grid_size, endpoint=False, dtype='int')
    grid_positions = list(product(positions, positions))
    gabors = landscape.get_gabors(grid_positions)

    stim_positions = gems.create_grid_positions(n_rows=grid_size, n_cols=grid_size,
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
def radius(ctx, grid_pos='10-10', search_radius=8):
    """Draw gabors in a given search radius."""
    grid_positions = gems.create_grid(search_radius, search_radius, centroid=pos_from_str(grid_pos))
