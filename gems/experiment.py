import subprocess
from os import path

import yaml

from psychopy import visual, core, event
import pandas

from .config import PKG_ROOT
from .landscape import *
from .display import create_radial_positions, create_grid_positions
from .util import get_subj_info, pos_to_str, pos_list_to_str
from .data import output_filepath_from_subj_info, DATA_COLUMNS
from .validation import check_output_filepath_exists, verify_subj_info_strings, parse_subj_info_strings


class Experiment(object):
    # Responses ----
    response_keys = ['space']
    response_text = 'Press SPACEBAR to continue'

    # Wait times ----
    duration_fix = 0.5
    duration_feedback = 1.5
    duration_iti = 1.0
    duration_break_minimum = 5

    # Window settings ----
    win_size = None  # no size means full screen
    win_color = (.6, .6, .6)

    # Stimulus presentation ----
    gabor_size = 60     # in pix
    n_search_items = 9  # gabors per trial
    stim_radius = 200   # pix between fix and center of grating stim

    # Players ----
    score = 0
    sight_radius = 8  # range of sight on the grid in the landscape
    pos = (0, 0)      # initial grid position on the landscape

    # Defaults ----
    text_kwargs = dict(font='Consolas', color='black', pos=(0,50))

    @classmethod
    def from_gui(cls, gui_yaml):
        """Create an experiment after obtaining condition vars from a GUI."""
        subj_info = get_subj_info(gui_yaml,
            check_exists=check_output_filepath_exists,
            verify=verify_subj_info_strings,
            save_order=True)
        subj_info = parse_subj_info_strings(subj_info)
        return cls(**subj_info)

    def __init__(self, **condition_vars):
        self.condition_vars = condition_vars
        self.texts = yaml.load(open(path.join(PKG_ROOT, 'texts.yaml')))

        self.stim_positions = \
            create_radial_positions(self.n_search_items, radius=self.stim_radius)

        self.grating_stim_kwargs = dict(
            win=self.win,
            size=self.gabor_size)

        self.trial_header = self.make_text('',
            pos=(0, self.win.size[1]/2-10),
            alignVert='top',
            height=30,
            bold=True)

        self.score_text = self.make_text('',
            pos=(-self.win.size[0]/2+10, self.win.size[1]/2-10),
            alignVert='top',
            alignHoriz='left',
            height=30,
            bold=True)

        self.fixation = self.make_text('+', height=30, pos=(0,0))

        # Object cache
        self._cache = {}

    def run(self):
        self.show_welcome()
        self.show_training()
        self.run_training_trials()
        self.show_test()
        self.run_test_trials()
        self.show_end()
        self.quit()

    def run_training_trials(self, n_training_trials=10):
        instructions_condition = self.get_var('instructions_condition')
        self.landscape = dict(
            orientation=OrientationBias(),
            spatial_frequency=SpatialFrequencyBias(),
        )[instructions_condition]

        self.pos = (0, 0)
        self.score = 0

        block_data = dict(
            landscape_ix=1,
            landscape_name=self.landscape.__name__,
            starting_pos=pos_to_str(self.pos),
            feedback='all',
        )

        for trial in range(n_training_trials):
            trial_data = self.run_trial(feedback='training')
            trial_data.update(block_data)
            trial_data['trial'] = trial
            self.write_trial(trial_data)

    def run_test_trials(self, n_test_trials=10):

        # The order of these landscapes is instruction-dependent
        landscapes = {
            0: SimpleHillA(),
            1: SimpleHillB(),
            2: SimpleHillC(),
            3: SimpleHillD(),
        }

        for landscape_ix, start_pos in enumerate(self.starting_positions):
            if quarry_ix > 0:
                self.show_break()

            self.landscape = landscapes[quarry_ix]
            self.pos = start_pos
            self.score = 0

            block_data = dict(
                landscape_ix=landscape_ix,
                landscape_name=self.landscape.__name__,
                starting_pos=pos_to_str(self.pos),
                feedback='selected',
            )

            for trial in range(n_test_trials):
                trial_data = self.run_trial(feedback='selected')
                trial_data.update(block_data)
                trial_data['trial'] = trial
                self.write_trial(trial_data)

    def run_trial(self, feedback='training'):
        gabors = self.landscape.sample_gabors(
            self.pos,
            self.search_radius,
            self.n_search_items
        )

        trial_data = dict(
            subj_id=self.get_var('subj_id'),
            date=self.get_var('date'),
            computer=self.get_var('computer'),
            experimenter=self.get_var('experimenter'),
            instructions=self.get_var('instructions_condition'),
            sight_radius=self.sight_radius,
            n_search_items=self.n_search_items,
            pos=pos_to_str(self.pos),
            stims=pos_list_to_str(gabors.keys()),
        )

        self.trial_header.text = self.get_trial_text('instructions')

        # Begin trial presentation ----

        self.trial_header.draw()
        self.draw_score()
        self.fixation.draw()
        self.win.flip()
        core.wait(self.duration_fix)

        self.trial_header.draw()
        self.draw_score()
        self.fixation.draw()
        for pos, grid_pos in zip(self.stim_positions, gabors.keys()):
            gabor = gabors[grid_pos]
            gabor.pos = pos
            gabor.draw()
        self.win.flip()

        grid_pos, gabor_pos, time = self.get_clicked_gabor(gabors)

        score = self.landscape.get_score(grid_pos)
        self.pos = grid_pos      # update current pos
        prev_score = self.score
        self.score += score      # update current score

        trial_data['selected'] = pos_to_str(grid_pos)
        trial_data['rt'] = round(time, 2)
        trial_data['score'] = score
        trial_data['total'] = self.score

        # Draw gabors again
        for gabor in gabors.values():
            gabor.draw()

        if feedback == 'training':
            self.give_training_feedback()
        elif feedback == 'selected':
            self.give_selected_feedback()

        self.draw_score()
        self.win.flip()

        core.wait(self.iti)
        return trial_data

    def give_training_feedback(self):
        self.mouse.clickReset()
        self.trial_header.text = self.get_trial_text('training_feedback')
        self.trial_header.draw()

        selected_label = self.label_gabor_score(score, gabor_pos, bold=True)
        self.draw_score(prev_score, score)

        # Draw selected label as green unless another is higher score
        selected_label.color = 'green'
        for other_grid_pos, gabor in gabors.items():
            if grid_pos == other_grid_pos:
                # the label for this pos has already been drawn
                continue
            other_score = self.landscape.get_score(other_grid_pos)
            other_label = self.label_gabor_score(other_score, gabor.pos)
            if other_score > score:
                other_label.color = 'green'
                selected_label.color = 'red'
            other_label.draw()

        selected_label.draw()
        self.win.flip()
        self.mouse.clickReset()

        while True:
            (left, _, _) = self.mouse.getPressed()
            if left:
                break

    def give_selected_feedback(self):
        selected_label = self.label_gabor_score(score, gabor_pos, bold=True)
        self.draw_score(prev_score, score)
        selected_label.draw()
        self.win.flip()
        core.wait(self.feedback_duration)

    def get_clicked_gabor(self, gabors):
        self.mouse.clickReset()
        while True:
            (left, _, _), (time, _, _) = self.mouse.getPressed(getTime=True)
            if left:
                pos = self.mouse.getPos()
                for grid_pos, gabor in gabors.items():
                    if gabor.contains(pos):
                        return grid_pos, gabor.pos, time

            keys = event.getKeys(keyList=['q'])
            if len(keys) > 0:
                key = keys[0]
                core.quit()

            core.wait(0.05)

    def label_gabor_score(self, score, gabor_pos, **kwargs):
        feedback_pos = (gabor_pos[0], gabor_pos[1]+(self.gabor_size/2))
        feedback = self.make_text('+'+str(score), pos=feedback_pos, height=24, alignVert='bottom', **kwargs)
        return feedback

    def draw_score(self, prev_score=None, delta=None):
        if prev_score is not None and delta:
            self.score_text.text = 'Your score:\n%s\n+%s\n----------\n%s' % (prev_score, delta, self.score)
        else:
            self.score_text.text = 'Your score:\n%s' % (self.score)
        self.score_text.draw()

    def show_welcome(self):
        self.make_title(self.texts['welcome'])

        instructions_text = self.texts['instructions'].format(
            response_text=self.response_text)
        self.make_text(instructions_text)

        self.make_explorer()

        left_gabor = self.landscape.get_grating_stim((10, 10))
        left_gabor.pos = (-100, -200)
        left_gabor.draw()

        right_gabor = self.landscape.get_grating_stim((20, 20))
        right_gabor.pos = (100, -200)
        right_gabor.draw()

        self.win.flip()
        event.waitKeys(keyList=['space'])

    def show_training(self):
        self.make_title(self.texts['training_title'])

        instructions_condition = self.condition_vars['instructions_condition']
        training_instructions = self.texts['training_instructions'][instructions_condition]
        instructions_text = self.texts['training'].format(
            training_instructions=training_instructions)
        self.make_text(instructions_text)

        left_gabor = self.landscape.get_grating_stim((10, 10))
        left_gabor.pos = (-100, -200)
        left_gabor.draw()

        right_gabor = self.landscape.get_grating_stim((20, 20))
        right_gabor.pos = (100, -200)
        right_gabor.draw()

        self.win.flip()

        self.mouse.clickReset()
        while True:
            (left, _, _) = self.mouse.getPressed()
            if left:
                pos = self.mouse.getPos()
                if right_gabor.contains(pos):
                    break

            core.wait(0.05)

    def show_test(self):
        self.make_title(self.texts['test_title'])
        self.make_text(self.texts['test'])
        self.make_explorer()
        self.win.flip()
        event.waitKeys(['space'])

    def show_break(self):
        title = self.make_title(self.texts['break_title'])
        text = self.make_text(self.texts['break'])
        explorer = self.make_explorer()

        self.win.flip()
        core.wait(self.break_minimum)

        title.draw()
        text.draw()
        explorer.draw()
        self.make_text(self.texts['break_complete'], pos=(0, 0))
        self.win.flip()
        event.waitKeys(['space'])

    def show_end(self):
        end_title = self.make_title(self.texts['end_title'])
        end = self.make_text(self.texts['end'])
        self.make_explorer()
        self.win.flip()
        event.waitKeys(keyList=self.response_keys)

    def make_text(self, text, draw=True, **kwargs):
        kw = self.text_kwargs.copy()
        kw.update(kwargs)
        text = visual.TextStim(self.win, text=text, **kw)
        if draw:
            text.draw()
        return text

    def make_title(self, text, draw=True, **kwargs):
        kw = dict(bold=True, height=30, pos=(0, 250))
        kw.update(kwargs)
        text = self.make_text(text, **kw)
        if draw:
            text.draw()
        return text

    def make_explorer(self, draw=True):
        explorer_png = path.join(PKG_ROOT, 'img', 'explorer.png')
        explorer = visual.ImageStim(self.win, explorer_png, pos=(0, -200), size=200)
        if draw:
            explorer.draw()
        return explorer

    @property
    def output(self):
        if 'output' in self._cache:
            return self._cache['output']

        self._cache['output'] = open(self.condition_vars['filename'], 'w', 1)

        # Write CSV header
        self.write_line(DATA_COLUMNS)

        return self._cache['output']

    def write_trial(self, trial_data):
        trial_strings = []
        for col_name in DATA_COLUMNS:
            datum = trial_data.get(col_name, '')
            trial_strings.append(str(datum))
        self.write_line(trial_strings)

    def write_line(self, list_of_strings):
        self.output.write(','.join(list_of_strings)+'\n')

    def quit(self):
        core.quit()
        self.output_file.close()


    def get_var(self, key):
        return self.condition_vars.get(key, '')

    def get_text(self, key):
        return self.texts.get(key, '')

    def get_trial_text(self, key):
        return self.get_text('trial').get(key, '')

    @property
    def win(self):
        if 'win' in self._cache:
            return self._cache['win']

        if self.win_size is None:
            fullscr = True
            self.win_size = (1, 1)
        else:
            fullscr = False

        win = visual.Window(self.win_size, fullscr=fullscr, units='pix',
                            color=self.win_color)

        # Update defaults with window-specific settings
        self.text_kwargs['wrapWidth'] = win.size[0] * 0.6

        self._cache['win'] = win
        return self._cache['win']

    @property
    def mouse(self):
        return self._cache.setdefault('mouse', event.Mouse())
