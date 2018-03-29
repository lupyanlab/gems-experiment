from os import path
from invoke import task
from psychopy import visual

import gems


@task
def trial(ctx, move_to_r_pkg=False):
    """Draw a trial screen."""
    win_size = (500, 500)
    gabor_size = 100
    display_radius = 120 

    win = visual.Window(size=win_size, units='pix', color=(0.6,0.6,0.6))
    visual.TextStim(win, text='Click on the gem you think is most valuable',
                    pos=(0, win_size[1]/2 - 10), alignVert='top', alignHoriz='center', font='Menlo',
                    color='black', wrapWidth=win_size[0]*0.6).draw()
    stim_positions = gems.create_radial_positions(6, radius=display_radius)
    landscape = gems.landscape.SimpleHill(seed=143)
    landscape.grating_stim_kwargs.update({'win': win, 'size': gabor_size})
    gabors = landscape.sample_gabors(6, (5, 5), 12)
    for (grid_pos, stim_pos) in zip(gabors.keys(), stim_positions):
        gabors[grid_pos].pos = stim_pos
        gabors[grid_pos].draw()
    win.flip()
    win.getMovieFrame()
    dst_dir = '../data/inst/extdata' if move_to_r_pkg else '.'
    dst = path.join(dst_dir, 'trial.png')
    win.saveMovieFrames(dst)
    ctx.run('open {}'.format(dst), echo=True)
