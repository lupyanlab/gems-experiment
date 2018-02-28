import subprocess
import webbrowser
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
    duration_feedback = 2
    duration_iti = 1.0
    duration_break_minimum = 5

    # Window settings ----
    win_size = None  # no size means full screen
    win_color = (.6, .6, .6)

    # Stimulus presentation ----
    gabor_size = 80     # in pix
    n_gabors = 6        # gabors per trial
    stim_radius = 200   # pix between fix and center of grating stim

    # Players ----
    total_score = 0
    sight_radius = 8  # range of sight on the grid in the landscape
    pos = (0, 0)      # initial grid position on the landscape
    n_training_trials = 25
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
            wrapWidth=self.win.size[0])

        self.trial_footer = self.make_text('',
            draw=False,
            pos=(0, -self.stim_radius*2),
            alignVert='bottom',
            height = 30,
            bold=True)

        self.score_text = self.make_text('',
            draw=False,
            pos=(self.stim_radius*3, self.stim_radius*1.8),
            alignVert='top',
            alignHoriz='right',
            color='blue',
            height=30)

        self.landscape_title = self.make_text('',
            draw=False,
            pos=(self.stim_radius*3, self.stim_radius*2),
            alignVert='top',
            alignHoriz='right',
            color='blue',
            height=30)

        self.fixation = self.make_text('+', draw=False, height=30, pos=(0,0))

        self.mouse = event.Mouse()

        self.use_landscape('SimpleHill')

        self.exp_timer = core.Clock()

    def run(self):
        self.exp_timer.reset()
        self.show_welcome()
        self.show_training()
        self.run_training_trials()
        self.show_test()
        self.run_test_trials()
        self.show_end()
        self.quit()

    def show_welcome(self, save_screenshot=False):
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
        if save_screenshot:
            self.save_screenshot('welcome_{}.png'.format(instructions_condition))
        event.waitKeys(keyList=self.response_keys)

    def show_training(self, save_screenshot=True):
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
        if save_screenshot:
            self.save_screenshot('training_{}.png'.format(instructions_condition))

        self.mouse.clickReset()
        while True:
            (left, _, _) = self.mouse.getPressed()
            if left:
                pos = self.mouse.getPos()
                if right_gabor.contains(pos):
                    break

            core.wait(0.05)

        self.make_title('Are you ready to begin?')
        self.make_text('You will now collect {} gems from the Training Quarry. Click anywhere to begin.'.format(self.n_training_trials))

        while True:
            (left, _, _) = self.mouse.getPressed()
            if not left:
                break

        self.win.flip()
        self.mouse.clickReset()
        while True:
            (left, _, _) = self.mouse.getPressed()
            if left:
                break

    def save_screenshot(self, name):
        self.win.getMovieFrame()
        self.win.saveMovieFrames(name)

    def run_training_trials(self):
        training_landscapes = dict(
            orientation=landscape.OrientationBias(),
            spatial_frequency=landscape.SpatialFrequencyBias(),
        )
        instructions_condition = self.get_var('instructions_condition')

        self.landscape = training_landscapes[instructions_condition]
        self.pos = (5, 5)
        self.total_score = self.landscape.score(self.pos)

        block_data = dict(
            landscape_ix=0,
            landscape_name=self.landscape.__class__.__name__,
            starting_pos=pos_to_str(self.pos),
            starting_score=self.total_score
        )

        for trial in range(self.n_training_trials):
            trial_data = self.run_trial(trial=trial, feedback='training', landscape_title='Training Quarry')
            trial_data.update(block_data)
            self.write_trial(trial_data)

    def show_test(self):
        self.make_title(self.texts['test_title'])
        self.make_text(self.texts['test'])
        self.make_explorer()
        self.win.flip()
        event.waitKeys(['space'])

        self.make_title('Are you ready to begin?')
        num_quarries = 4
        self.make_text('You will now travel to {} different quarries and collect {} gems at each one. Click anywhere to begin.'.format(num_quarries, self.n_trials_per_block))

        while True:
            (left, _, _) = self.mouse.getPressed()
            if not left:
                break

        self.win.flip()
        self.mouse.clickReset()
        while True:
            (left, _, _) = self.mouse.getPressed()
            if left:
                break

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
            self.total_score = self.landscape.score(start_pos)

            block_data = dict(
                landscape_ix=landscape_ix+1,
                landscape_name=self.landscape.__class__.__name__,
                starting_pos=pos_to_str(self.pos),
                starting_score=self.total_score
            )

            for trial in range(self.n_trials_per_block):
                trial_data = self.run_trial(trial=trial, feedback='selected', landscape_title='Quarry #{}'.format(landscape_ix+1))
                trial_data.update(block_data)
                self.write_trial(trial_data)

    def show_end(self):
        end_title = self.make_title(self.texts['end_title'])
        end = self.make_text(self.texts['end'])
        self.make_explorer()
        self.win.flip()
        event.waitKeys(keyList=self.response_keys)

        prefilled_url = self.get_text('survey').format(**self.condition_vars)
        webbrowser.open(prefilled_url)
        with open('survey-links.txt', 'a') as f:
            f.write(prefilled_url + '\n')

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

    def run_trial(self, trial=0, feedback='training', landscape_title=''):
        gabors = self.sample_gabors()
        trial_data = self.make_trial_data(feedback=feedback,
                                          stims=pos_list_to_str(gabors.keys()),
                                          trial=trial)

        self.landscape_title.text = landscape_title

        # Begin trial presentation ----
        self.fixation.draw()
        self.landscape_title.draw()
        if trial > 0:
            self.draw_score()
        self.win.flip()
        core.wait(self.duration_fix)

        self.trial_header.text = self.get_trial_text('instructions')
        self.trial_header.draw()
        self.landscape_title.draw()
        if trial > 0:
            self.draw_score()
        self.fixation.draw()
        for gabor in gabors.values():
            gabor.draw()
        self.win.flip()

        grid_pos, time = self.get_clicked_gabor(gabors)
        trial_data['exp_time'] = self.exp_timer.getTime()

        # Compare selected gem to prev trial gem
        prev_gem_score = self.landscape.score(self.pos)
        new_gem_score = self.landscape.score(grid_pos)
        diff_from_prev_gem = new_gem_score - prev_gem_score

        prev_grid_pos = self.pos
        self.pos = grid_pos               # move to new pos
        self.total_score = new_gem_score  # update total score

        if feedback == 'training':
            self.give_training_feedback(gabors, prev_grid_pos, grid_pos, trial)
        elif feedback == 'selected':
            self.give_selected_feedback(gabors, prev_grid_pos, grid_pos, trial)

        trial_data['selected'] = pos_to_str(grid_pos)
        trial_data['rt'] = round(time, 2)
        trial_data['score'] = new_gem_score
        trial_data['delta'] = diff_from_prev_gem

        self.landscape_title.draw()
        self.draw_score()
        self.win.flip()
        core.wait(self.duration_iti)

        return trial_data

    def give_training_feedback(self, gabors, prev_grid_pos, selected_grid_pos, trial):
        self.trial_header.text = self.get_trial_text('training_feedback')


        prev_score = self.landscape.score(prev_grid_pos)
        selected_score = self.landscape.score(selected_grid_pos)

        selected_gabor = gabors[selected_grid_pos]
        highlight = self.highlight_selected(selected_gabor.pos, lineColor='black')

        most_valuable_grid_pos = selected_grid_pos
        most_valuable_grid_pos_list = []
        most_valuable_score = self.landscape.score(selected_grid_pos)

        for grid_pos, gabor in gabors.items():
            gabor.draw()

            score = self.landscape.score(grid_pos)
            delta = score - prev_score

            if trial == 0:
                # On the first trial, show actual scores, not deltas.
                delta = score

            label = self.label_gabor_score(delta, gabor.pos)
            label.draw()

            if score > most_valuable_score:
                # Update the most valuable gabor
                most_valuable_grid_pos = grid_pos
                most_valuable_grid_pos_list = [grid_pos, ]
                most_valuable_score = score
            elif score == most_valuable_score:
                most_valuable_grid_pos_list.append(grid_pos)

        self.landscape_title.draw()
        self.trial_header.draw()
        if trial == 0:
            prev_score = None
        self.draw_score(prev_score)
        highlight.draw()
        self.win.flip()
        self.get_clicked_gabor(gabors, most_valuable_grid_pos_list)

    def give_selected_feedback(self, gabors, prev_grid_pos, selected_grid_pos, trial):
        prev_score = self.landscape.score(prev_grid_pos)
        selected_score = self.landscape.score(selected_grid_pos)
        delta = selected_score - prev_score

        selected_gabor = gabors[selected_grid_pos]
        highlight = self.highlight_selected(selected_gabor.pos, lineColor='black')

        if trial == 0:
            # On first trial, show actual scores, not deltas.
            delta = selected_score

        selected_label = self.label_gabor_score(delta, selected_gabor.pos)

        for gabor in gabors.values():
            gabor.draw()

        highlight.draw()
        selected_label.draw()
        if trial == 0:
            prev_score = None
        self.draw_score(prev_score)
        self.landscape_title.draw()
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

        # Wait to get a new mouse response until they have let go of the mouse
        while True:
            (left, _, _) = self.mouse.getPressed()
            if not left:
                break

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
        if score >= 0:
            score_str = '+' + str(score)
            color = 'green'
        else:
            score_str = str(score)
            color = 'red'

        feedback_pos = (gabor_pos[0], gabor_pos[1]+self.gabor_size/2+10)
        feedback = self.make_text(score_str, pos=feedback_pos, height=30, alignVert='bottom', color=color, **kwargs)
        return feedback

    def highlight_selected(self, gabor_pos, **kwargs):
        circle = visual.Circle(self.win, pos=gabor_pos, radius=(self.gabor_size/2)+10, lineWidth=2, **kwargs)
        return circle

    def draw_score(self, prev_score=None):
        if prev_score is None:
            self.score_text.text = 'Your score: %s' % (self.total_score)
        else:
            delta = self.total_score - prev_score
            self.score_text.text = 'Previous score: %s\n     New score: %s' % (prev_score, self.total_score)
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
        kw = dict(bold=True, height=30, pos=(0, 270), wrapWidth=self.win.size[0])
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
        self.text_kwargs['wrapWidth'] = win.size[0] * 0.5
        self.grating_stim_kwargs['win'] = win

        self._cache['win'] = win
        return self._cache['win']

    def use_landscape(self, name):
        self.landscape = getattr(landscape, name)()
        self.landscape.grating_stim_kwargs.update(self.grating_stim_kwargs)
