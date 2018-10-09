from os import path
from invoke import task
from psychopy import visual

import gems


@task
def trial(ctx, move_to_r_pkg=False):
    """Draw a trial screen."""
    win_size = (500, 500)
    gabor_size = 60
    display_radius = 120
    sight_radius = 8

    win = visual.Window(size=win_size, units='pix', color=(0.6,0.6,0.6))
    visual.TextStim(win, text='Click on a gem you think is more valuable than the last one.',
                    pos=(0, win_size[1]/2 - 40), alignVert='top', alignHoriz='center', font='Menlo',
                    color='black', wrapWidth=win_size[0]*0.9).draw()
    stim_positions = gems.create_line_positions(6, screen_width=win.size[0]-(2*gabor_size), y_pos=85)
    landscape = gems.landscape.SimpleHill(seed=143)
    landscape.grating_stim_kwargs.update({'win': win, 'size': gabor_size})
    gabors = landscape.sample_gabors(6, (10, 10), radius=sight_radius)
    for (grid_pos, stim_pos) in zip(gabors.keys(), stim_positions):
        gabors[grid_pos].pos = stim_pos
        gabors[grid_pos].draw()
        print(grid_pos)

    visual.TextStim(win, text='Here is the gem you selected last.',
                    pos=(0, -125), alignVert='top', alignHoriz='center', font='Menlo',
                    color='black', wrapWidth=win_size[0]*0.9).draw()
    prev_gem = landscape.get_grating_stim((10, 10))
    prev_gem.pos = (0, -90)
    prev_gem.draw()

    win.flip()
    win.getMovieFrame()
    dst_dir = '../data/inst/extdata' if move_to_r_pkg else '.'
    dst = path.join(dst_dir, 'trial.png')
    win.saveMovieFrames(dst)
    ctx.run('open {}'.format(dst), echo=True)
