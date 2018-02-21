import subprocess
from os import path

import yaml

import pandas
from psychopy import visual, core, event

from . import landscape
from .config import pkg_root
from .display import create_radial_positions
from .util import get_subj_info, pos_to_str, pos_list_to_str
from .data import make_output_filepath, check_output_filepath, data_columns
from .conditions import verify_condition_vars, convert_condition_vars


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
    n_gabors = 9  # gabors per trial
    stim_radius = 200   # pix between fix and center of grating stim

    # Players ----
    total_score = 0
    sight_radius = 8  # range of sight on the grid in the landscape
    pos = (0, 0)      # initial grid position on the landscape
    n_training_trials = 10
    n_trials_per_block = 50

    # Defaults ----
    text_kwargs = dict(font='Consolas', color='black', pos=(0,50))
    grating_stim_kwargs = dict(size=gabor_size)

    @classmethod
    def from_gui(cls, gui_yaml):
        """Create an experiment after obtaining condition vars from a GUI."""
        subj_info = get_subj_info(gui_yaml,
            check_exists=check_output_filepath,
            verify=verify_condition_vars,
            save_order=True)
        subj_info = convert_condition_vars(subj_info)
        return cls(**subj_info)

    def __init__(self, **condition_vars):
        self.condition_vars = condition_vars
        self.texts = yaml.load(open(path.join(pkg_root, 'texts.yaml')))
        self._cache = {}

        self.stim_positions = \
            create_radial_positions(self.n_gabors, radius=self.stim_radius)

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

    def run_training_trials(self):
        training_landscapes = dict(
            orientation=landscape.OrientationBias(),
            spatial_frequency=landscape.SpatialFrequencyBias(),
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

        for trial in range(self.n_training_trials):
            trial_data = self.run_trial(trial=trial, feedback='training')
            trial_data.update(block_data)
            self.write_trial(trial_data)

    def show_test(self):
        self.make_title(self.texts['test_title'])
        self.make_text(self.texts['test'])
        self.make_explorer()
        self.win.flip()
        event.waitKeys(['space'])

    def run_test_trials(self):
        condition = self.get_var('instructions_condition')

        ordered_landscapes = dict(
            orientation=['SimpleHill', 'ReverseSpatialFrequency', 'ReverseOrientation', 'ReverseBoth'],
            spatial_frequency=['SimpleHill', 'ReverseOrientation', 'ReverseSpatialFrequency', 'ReverseBoth'],
        )
        landscapes = ordered_landscapes[condition]

        for landscape_ix, start_pos in enumerate(self.get_var('starting_positions')):
            if landscape_ix > 0:
                self.show_break()

            # 'SimpleHill' -> landscape.SimpleHill()
            self.landscape = getattr(landscape, landscapes[landscape_ix])()
            self.pos = start_pos
            self.total_score = 0

            block_data = dict(
                landscape_ix=landscape_ix+1,
                landscape_name=self.landscape.__class__.__name__,
                starting_pos=pos_to_str(self.pos),
            )

            for trial in range(self.n_trials_per_block):
                trial_data = self.run_trial(trial=trial, feedback='summary')
                trial_data.update(block_data)
                self.write_trial(trial_data)

    def show_end(self):
        end_title = self.make_title(self.texts['end_title'])
        end = self.make_text(self.texts['end'])
        self.make_explorer()
        self.win.flip()
        event.waitKeys(keyList=self.response_keys)

    def sample_gabors(self):
        """Sample gabors in a certain radius and place them on the screen.

        Returns a dict with landscape position keys and GratingStim values.
        """
        gabors = self.landscape.sample_gabors(self.n_gabors, self.pos,
                                              self.sight_radius)
        for gabor, pos in zip(gabors.values(), self.stim_positions):
            gabor.pos = pos

        return gabors

    def make_trial_data(self, **kwargs):
        trial_data = dict(
            subj_id = self.get_var('subj_id'),
            date = self.get_var('date'),
            computer = self.get_var('computer'),
            experimenter = self.get_var('experimenter'),
            instructions = self.get_var('instructions_condition'),
            sight_radius = self.sight_radius,
            n_gabors = self.n_gabors,
            pos = pos_to_str(self.pos)
        )
        trial_data.update(kwargs)
        return trial_data

    def run_trial(self, trial=0, feedback='training'):
        gabors = self.sample_gabors()
        trial_data = self.make_trial_data(feedback=feedback,
                                          stims=pos_list_to_str(gabors.keys()),
                                          trial=trial)

        # Begin trial presentation ----
        self.fixation.draw()
        self.win.flip()
        core.wait(self.duration_fix)

        self.trial_header.text = self.get_trial_text('instructions')
        self.trial_header.draw()
        self.fixation.draw()
        for gabor in gabors.values():
            gabor.draw()
        self.win.flip()

        grid_pos, time = self.get_clicked_gabor(gabors)

        # Compare selected gem to prev trial gem
        prev_gem_score = self.landscape.score(self.pos)
        new_gem_score = self.landscape.score(grid_pos)
        diff_from_prev_gem = new_gem_score - prev_gem_score

        prev_grid_pos = self.pos
        self.pos = grid_pos               # move to new pos
        self.total_score += new_gem_score # update total score

        if feedback == 'training':
            self.give_training_feedback(gabors, grid_pos)
        elif feedback == 'summary':
            self.give_selected_feedback(gabors, grid_pos)
            self.show_trial_summary(trial, new_gem_score, diff_from_prev_gem, prev_grid_pos, grid_pos)

        trial_data['selected'] = pos_to_str(grid_pos)
        trial_data['rt'] = round(time, 2)
        trial_data['score'] = new_gem_score
        trial_data['delta'] = diff_from_prev_gem
        trial_data['total'] = self.total_score

        self.win.flip()
        core.wait(self.duration_iti)

        return trial_data

    def show_trial_summary(self, trial, new_score, diff_from_prev_gem, prev_grid_pos, new_grid_pos):
        if trial == 0:
            self.show_summary_first_trial(new_score, new_grid_pos)
        else:
            if diff_from_prev_gem > 0:
                self.show_summary_improve(new_score, diff_from_prev_gem, new_grid_pos, prev_grid_pos)
            elif diff_from_prev_gem < 0:
                self.show_summary_decrease(new_score, abs(diff_from_prev_gem), new_grid_pos, prev_grid_pos)
            else: # diff_from_prev_gem == 0
                self.show_summary_same(new_score, new_grid_pos)

    def show_summary_first_trial(self, new_score, selected_grid_pos):
        self.make_summary(new_score)
        self.make_text(self.get_trial_text('summary_first_trial'), pos=(0, 50))

        gabor = self.landscape.get_grating_stim(selected_grid_pos)
        gabor.pos = (0, 100)
        gabor.draw()

        highlight = self.highlight_selected(gabor.pos, lineColor='green')
        highlight.draw()

        self.win.flip()
        self.get_click(after=1.0)

    def show_summary_improve(self, new_score, diff_from_prev_gem, prev_grid_pos, new_grid_pos):
        self.make_summary(new_score)
        summary = self.get_trial_text('summary_improve').format(
            diff_from_prev_gem=diff_from_prev_gem
        )
        self.make_text(summary, color='green', pos=(0, 0))

        prev_gabor = self.landscape.get_grating_stim(prev_grid_pos)
        prev_gabor.pos = (-100, 100)
        prev_gabor.draw()

        new_gabor = self.landscape.get_grating_stim(new_grid_pos)
        new_gabor.pos = (100, 100)
        new_gabor.draw()

        highlight = self.highlight_selected(new_gabor.pos, lineColor='green')
        highlight.draw()

        self.win.flip()
        self.get_click()

    def show_summary_decrease(self, new_score, diff_from_prev_gem, prev_grid_pos, new_grid_pos):
        self.make_summary(new_score)
        summary = self.get_trial_text('summary_decrease').format(
            diff_from_prev_gem=diff_from_prev_gem
        )
        self.make_text(summary, color='red', pos=(0, 0))

        prev_gabor = self.landscape.get_grating_stim(prev_grid_pos)
        prev_gabor.pos = (-100, 100)
        prev_gabor.draw()

        new_gabor = self.landscape.get_grating_stim(new_grid_pos)
        new_gabor.pos = (100, 100)
        new_gabor.draw()

        highlight = self.highlight_selected(new_gabor.pos, lineColor='red')
        highlight.draw()

        self.win.flip()
        self.get_click()

    def show_summary_same(self, new_score, new_grid_pos):
        self.make_summary(new_score)
        summary = self.get_trial_text('summary_same').format(
            new_score=new_score,
            total=self.total_score
        )
        self.make_text(summary, pos=(0, 0))

        new_gabor = self.landscape.get_grating_stim(new_grid_pos)
        new_gabor.pos = (0, 100)
        new_gabor.draw()

        highlight = self.highlight_selected(new_gabor.pos, lineColor='green')
        highlight.draw()

        self.win.flip()
        self.get_click()

    def make_summary(self, new_score):
        self.make_title(self.get_trial_text('summary').format(new_score=new_score, total_score=self.total_score))
        self.make_text('Click anywhere to continue.', pos=(0, -50))

    def get_click(self, after=0.5):
        core.wait(after)
        self.mouse.clickReset()
        while True:
            (left, _, _) = self.mouse.getPressed()
            if left:
                break
            core.wait(0.01)

    def give_training_feedback(self, gabors, selected_grid_pos):
        self.trial_header.text = self.get_trial_text('training_feedback')

        selected_gabor = gabors[selected_grid_pos]
        highlight = self.highlight_selected(selected_gabor.pos, lineColor='green')

        most_valuable_grid_pos = selected_grid_pos
        most_valuable_grid_pos_list = []
        most_valuable_score = self.landscape.score(selected_grid_pos)
        selected_score = self.landscape.score(selected_grid_pos)

        for grid_pos, gabor in gabors.items():
            gabor.draw()

            score = self.landscape.score(grid_pos)
            label = self.label_gabor_score(score, gabor.pos)
            label.draw()

            delta = score - selected_score

            if score > selected_score:
                # The most valuable gabor was not selected
                highlight.lineColor = 'red'

            if score > most_valuable_score:
                # Update the most valuable gabor
                most_valuable_grid_pos = grid_pos
                most_valuable_grid_pos_list = [grid_pos, ]
                most_valuable_score = score
            elif score == most_valuable_score:
                most_valuable_grid_pos_list.append(grid_pos)

        self.trial_header.draw()
        highlight.draw()
        self.win.flip()
        self.get_clicked_gabor(gabors, most_valuable_grid_pos_list)

    def give_selected_feedback(self, gabors, selected_grid_pos):
        for gabor in gabors.values():
            gabor.draw()

        selected_gabor = gabors[selected_grid_pos]
        highlight = self.highlight_selected(selected_gabor.pos, lineColor='green')
        highlight.draw()
        selected_score = self.landscape.score(selected_grid_pos)
        selected_label = self.label_gabor_score(selected_score, selected_gabor.pos)
        selected_label.draw()
        self.win.flip()
        core.wait(self.duration_feedback)

    def get_clicked_gabor(self, gabors, target=None):
        if target is None:
            targets = gabors.copy()
        elif isinstance(target, list):
            assert all(t in gabors for t in target)
            targets = {t: gabors[t] for t in target}
        else:
            assert target in gabors
            targets = {target: gabors[target]}

        self.mouse.clickReset()
        waiting_for_response = True
        while waiting_for_response:
            core.wait(0.01)
            (left_click, _, _), (time, _, _) = self.mouse.getPressed(getTime=True)
            if left_click:
                pos = self.mouse.getPos()
                for grid_pos, gabor in targets.items():
                    if gabor.contains(pos):
                        waiting_for_response = False
                        break

        return grid_pos, time

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
        self.make_text(self.texts['break_complete'], pos=(0, -50))
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
        explorer_png = path.join(pkg_root, 'img', 'explorer.png')
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
        self.write_line(data_columns)

        return self._cache['output']

    def write_trial(self, trial_data):
        trial_strings = []
        for col_name in data_columns:
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
