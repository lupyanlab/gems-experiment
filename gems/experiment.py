import subprocess
from os import path

import yaml

from psychopy import visual, core, event
import pandas

from .config import PKG_ROOT
from . import landscape
from .landscape import *
from .display import create_radial_positions, create_grid_positions
from .util import get_subj_info, pos_to_str, pos_list_to_str
from .data import output_filepath_from_subj_info, DATA_COLUMNS
from .validation import check_output_filepath_exists, verify_subj_info_strings, parse_subj_info_strings


class Experiment(object):
    # Responses ----
    response_keys = ['space']
    response_text = 'Press SPACEBAR to continue'

    # Wait times in seconds ----
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
    total_score = 0
    sight_radius = 8  # range of sight on the grid in the landscape
    pos = (0, 0)      # initial grid position on the landscape

    # Defaults ----
    text_kwargs = dict(font='Consolas', color='black', pos=(0,50))
    grating_stim_kwargs = dict(size=gabor_size)

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
        self._cache = {}

        self.stim_positions = \
            create_radial_positions(self.n_search_items, radius=self.stim_radius)

        self.trial_header = self.make_text('',
            draw=False,
            pos=(0, self.stim_radius*2),
            alignVert='top',
            height=30,
            bold=True)

        self.trial_footer = self.make_text('',
            draw=False,
            pos=(0, -self.stim_radius*2),
            alignVert='bottom',
            height = 30,
            bold=True)

        self.score_text = self.make_text('',
            draw=False,
            pos=(-self.stim_radius*2.5, self.stim_radius*2),
            alignVert='top',
            alignHoriz='left',
            color='gold',
            height=30,
            bold=True)

        self.fixation = self.make_text('+', draw=False, height=30, pos=(0,0))

        self.mouse = event.Mouse()

    def run(self):
        self.show_welcome()
        self.show_training()
        self.run_training_trials()
        self.show_test()
        self.run_test_trials()
        self.show_end()
        self.quit()

    def show_welcome(self):
        instructions_text = self.get_text('instructions').format(
            response_text=self.response_text)

        left_gabor = self.landscape.get_grating_stim((10, 10))
        left_gabor.pos = (-100, -200)

        right_gabor = self.landscape.get_grating_stim((20, 20))
        right_gabor.pos = (100, -200)

        self.make_title(self.get_text('welcome'))
        self.make_text(instructions_text)
        self.make_explorer()
        left_gabor.draw()
        right_gabor.draw()
        self.win.flip()
        event.waitKeys(keyList=self.response_keys)

    def show_training(self):
        instructions_condition = self.get_var('instructions_condition')
        training_instructions = self.get_text('training_instructions')[instructions_condition]
        instructions_text = self.get_text('training').format(
            training_instructions=training_instructions)

        left_gabor = self.landscape.get_grating_stim((10, 10))
        left_gabor.pos = (-100, -200)

        right_gabor = self.landscape.get_grating_stim((20, 20))
        right_gabor.pos = (100, -200)

        self.make_title(self.get_text('training_title'))
        self.make_text(instructions_text)
        left_gabor.draw()
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

    def run_training_trials(self, n_training_trials=10):
        training_landscapes = dict(
            orientation=OrientationBias(),
            spatial_frequency=SpatialFrequencyBias(),
        )
        instructions_condition = self.get_var('instructions_condition')

        self.landscape = training_landscapes[instructions_condition]
        self.pos = (0, 0)
        self.total_score = 0

        block_data = dict(
            landscape_ix=0,
            landscape_name=self.landscape.__class__.__name__,
            starting_pos=pos_to_str(self.pos),
        )

        for trial in range(n_training_trials):
            trial_data = self.run_trial(feedback='training')
            trial_data.update(block_data)
            trial_data['trial'] = trial
            self.write_trial(trial_data)

    def show_test(self):
        self.make_title(self.texts['test_title'])
        self.make_text(self.texts['test'])
        self.make_explorer()
        self.win.flip()
        event.waitKeys(['space'])

    def run_test_trials(self, n_test_trials=10):
        condition = self.get_var('instruction_condition')
        ordered_landscapes = dict(
            orientation=[SimpleHill(), ReverseSpatialFrequency(), ReverseOrientation(), ReverseBoth()],
            spatial_frequency=[SimpleHill(), ReverseOrientation(), ReverseSpatialFrequency(), ReverseBoth()],
        )
        landscapes = ordered_landscapes[condition]

        for landscape_ix, start_pos in enumerate(self.starting_positions):
            if landscape_ix > 0:
                self.show_break()

            self.landscape = landscapes[landscape_ix]
            self.pos = start_pos
            self.total_score = 0

            block_data = dict(
                landscape_ix=landscape_ix+1,
                landscape_name=self.landscape.__class__.__name__,
                starting_pos=pos_to_str(self.pos),
            )

            for trial in range(n_test_trials):
                trial_data = self.run_trial(feedback='selected')
                trial_data.update(block_data)
                trial_data['trial'] = trial
                self.write_trial(trial_data)

    def show_end(self):
        end_title = self.make_title(self.texts['end_title'])
        end = self.make_text(self.texts['end'])
        self.make_explorer()
        self.win.flip()
        event.waitKeys(keyList=self.response_keys)

    def run_trial(self, feedback='training'):
        gabors = self.landscape.sample_gabors(
            self.pos,
            self.sight_radius,
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
            feedback=feedback,
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
        for gabor_pos, grid_pos in zip(self.stim_positions, gabors.keys()):
            gabor = gabors[grid_pos]
            gabor.pos = gabor_pos
            gabor.draw()
        self.win.flip()

        # Get trial response
        grid_pos, gabor_pos, time = self.get_clicked_gabor(gabors)

        # Compare selected gem to prev trial gem
        prev_gem_score = self.landscape.get_score(self.pos)
        new_gem_score = self.landscape.get_score(grid_pos)
        diff_from_prev_gem = new_gem_score - prev_gem_score

        if feedback == 'training':
            self.give_training_feedback(gabors, new_gem_score, grid_pos, gabor_pos)
        elif feedback == 'selected':
            self.give_selected_feedback(gabors, new_gem_score, grid_pos, gabor_pos)

        self.pos = grid_pos               # move to new pos
        self.total_score += new_gem_score # update total score

        trial_data['selected'] = pos_to_str(grid_pos)
        trial_data['rt'] = round(time, 2)
        trial_data['score'] = new_gem_score
        trial_data['delta'] = diff_from_prev_gem
        trial_data['total'] = self.total_score

        self.win.flip()
        core.wait(self.duration_iti)

        return trial_data

    def give_training_feedback(self, gabors, selected_score, selected_grid_pos, selected_gabor_pos):
        self.trial_header.text = self.get_trial_text('training_feedback')
        self.trial_footer.text = self.get_trial_text('training_continue')

        highlight = self.highlight_selected(selected_gabor_pos, lineColor='green')
        selected_label = self.label_gabor_score(selected_score, selected_gabor_pos, bold=True)

        # Assume the most valuable gabor is the one selected,
        # then update it later on.
        most_valuable_gabor = gabors[selected_grid_pos]
        most_valuable_gabor_score = selected_score

        for grid_pos, gabor in gabors.items():
            gabor.draw()

            if grid_pos == selected_grid_pos:
                # Don't draw label for selected gabor
                continue

            score = self.landscape.get_score(grid_pos)
            label = self.label_gabor_score(score, gabor.pos)

            delta = score - selected_score

            if delta > 0:
                # the most valuable gabor was not selected
                highlight.lineColor = 'red'

            if score > most_valuable_gabor_score:
                # update the most valuable gabor
                most_valuable_gabor = gabor
                most_valuable_gabor_score = score
                target_gabor = {grid_pos: gabor}

            label.draw()

        self.trial_header.draw()
        self.trial_footer.draw()
        self.draw_score()
        highlight.draw()
        selected_label.draw()

        self.win.flip()


        self.get_clicked_gabor(target_gabor)
        self.mouse.clickReset()

    def give_selected_feedback(self, gabors, selected_score, selected_grid_pos, selected_gabor_pos):
        for grid_pos, gabor in gabors.items():
            gabor.draw()

        selected_label = self.label_gabor_score(selected_score, selected_gabor_pos, bold=True)
        self.draw_score(prev_score, score)
        selected_label.draw()
        self.win.flip()

        core.wait(self.duration_feedback)

    def get_clicked_gabor(self, gabors):
        self.mouse.clickReset()
        while True:
            (left, _, _), (time, _, _) = self.mouse.getPressed(getTime=True)
            if left:
                pos = self.mouse.getPos()
                print('got a mouse click at: %s' % pos)
                for grid_pos, gabor in gabors.items():
                    if gabor.contains(pos):
                        print('mouse click was inside a gabor')
                        return grid_pos, gabor.pos, time

            keys = event.getKeys(keyList=['q'])
            if len(keys) > 0:
                key = keys[0]
                core.quit()

            core.wait(0.01)

    def label_gabor_score(self, score, gabor_pos, **kwargs):
        feedback_pos = (gabor_pos[0], gabor_pos[1]+self.gabor_size/2+10)
        feedback = self.make_text('$'+str(score), pos=feedback_pos, height=30, color='gold', alignVert='bottom', **kwargs)
        return feedback

    def highlight_selected(self, gabor_pos, **kwargs):
        circle = visual.Circle(self.win, pos=gabor_pos, radius=(self.gabor_size/2)+10, lineWidth=2, **kwargs)
        return circle

    def draw_score(self, prev_score=None, delta=None):
        if prev_score is not None and delta:
            self.score_text.text = 'Your score:\n%s\n+%s\n----------\n%s' % (prev_score, delta, self.total_score)
        else:
            self.score_text.text = 'Your score:\n%s' % (self.total_score)
        self.score_text.draw()

    def show_break(self):
        title = self.make_title(self.texts['break_title'])
        text = self.make_text(self.texts['break'])
        explorer = self.make_explorer()

        self.win.flip()
        core.wait(self.duration_break_minimum)

        title.draw()
        text.draw()
        explorer.draw()
        self.make_text(self.texts['break_complete'], pos=(0, -10))
        self.win.flip()
        event.waitKeys(['space'])

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
        self.output.close()

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
        self.grating_stim_kwargs['win'] = win

        self._cache['win'] = win
        return self._cache['win']

    def use_landscape(self, name):
        self.landscape = getattr(landscape, name)()
        self.landscape.grating_stim_kwargs.update(self.grating_stim_kwargs)
