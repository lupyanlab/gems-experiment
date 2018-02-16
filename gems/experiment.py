import subprocess
from os import path

import yaml

from psychopy import visual, core, event

from .config import PKG_ROOT
from .landscape import SimpleHill
from .display import create_stim_positions
from .util import get_subj_info, pos_to_str, pos_list_to_str
from .data import output_filepath_from_subj_info, DATA_COLUMNS
from .validation import check_output_filepath_exists, verify_subj_info_strings, parse_subj_info_strings


class Experiment(object):
    response_keys = ['space']
    response_text = 'Press SPACEBAR to continue'
    text_kwargs = dict(font='Consolas', color='black', pos=(0,50))

    # Duration of scoring feedback given on test trials.
    feedback_duration = 1.5
    iti = 1.0
    break_minimum = 5  # breaks must be 5 seconds long

    _win = None
    _mouse = None
    _output_file = None

    win_size = None
    win_color = (.6, .6, .6)
    gabor_size = 60

    n_search_items = 9
    search_radius = 8
    training_pos = (10, 10)
    starting_pos = (10, 10)
    pos = (0, 0)

    @classmethod
    def from_gui(cls, gui_yaml):
        subj_info = get_subj_info(gui_yaml,
            check_exists=check_output_filepath_exists,
            verify=verify_subj_info_strings,
            save_order=True)
        subj_info = parse_subj_info_strings(subj_info)
        return cls(**subj_info)

    def __init__(self, **condition_vars):
        self.condition_vars = condition_vars

        self.texts = yaml.load(open(path.join(PKG_ROOT, 'texts.yaml')))

        n_rows, n_cols = 3, 3
        assert n_rows * n_cols == self.n_search_items
        self.stim_positions = create_stim_positions(n_rows=3, n_cols=3,
            win_size=(self.win.size[1], self.win.size[1]), stim_size=(self.gabor_size * 4))

        self.landscape = SimpleHill()
        self.landscape.grating_stim_kwargs = dict(
            win=self.win,
            size=self.gabor_size)

        self.score = 0

        self.trial_header = self.make_text('',
            pos=(0, self.win.size[1]/2-10),
            alignVert='top',
            height=30,
            bold=True
        )

        self.score_text = self.make_text('',
            pos=(-self.win.size[0]/2 + 10, self.win.size[1]/2 - 10),
            alignVert='top',
            alignHoriz='left',
            height=30,
            bold=True
        )

    def run(self):
        self.show_welcome()
        self.show_training()
        self.run_training_trials()
        self.show_test()
        self.run_test_trials()
        self.show_end()
        self.quit()

    @property
    def win(self):
        if self._win is not None:
            return self._win

        if self.win_size is None:
            fullscr = True
            self.win_size = (1, 1)  # irrelevant
        else:
            fullscr = False
        self._win = visual.Window(self.win_size, fullscr=fullscr, units='pix',
                                  color=self.win_color)

        self.text_kwargs['wrapWidth'] = self._win.size[0] * 0.7
        return self._win

    @property
    def mouse(self):
        if self._mouse is None:
            self.win  # ensure window has been created
            self._mouse = event.Mouse()
        return self._mouse

    @property
    def output_file(self):
        if self._output_file is not None:
            return self._output_file

        output_filepath = output_filepath_from_subj_info(self.condition_vars)
        self._output_file = open(output_filepath, 'w', 1)

        # Write CSV header
        self.write_line(DATA_COLUMNS)

        return self.output_file

    def run_training_trials(self, n_training_trials=10):
        # Set pos to training pos
        quarry_start_pos = self.condition_vars.get('training_pos', self.training_pos)
        self.pos = quarry_start_pos
        for trial in range(n_training_trials):
            trial_data = self.run_trial(training=True)
            trial_data['quarry'] = 0
            trial_data['starting_pos'] = pos_to_str(quarry_start_pos)
            trial_data['feedback'] = 'all'
            trial_data['trial'] = trial

            self.write_trial(trial_data)

    def run_test_trials(self, n_test_trials=10):
        quarry_start_pos = self.condition_vars.get('starting_pos', self.starting_pos)
        self.pos = quarry_start_pos
        for trial in range(n_test_trials):
            trial_data = self.run_trial()
            trial_data['quarry'] = 1
            trial_data['starting_pos'] = pos_to_str(quarry_start_pos)
            trial_data['feedback'] = 'selected'
            trial_data['trial'] = trial

            self.write_trial(trial_data)

    def run_trial(self, training=False):
        self.draw_score()

        self.trial_header.text = self.texts['trial']['instructions']
        self.trial_header.draw()

        gabors = self.landscape.sample_gabors(
            self.pos,
            self.search_radius,
            self.n_search_items
        )

        trial_data = dict(
            subj_id=self.condition_vars.get('subj_id', ''),
            date=self.condition_vars.get('date', ''),
            computer=self.condition_vars.get('computer', ''),
            experimenter=self.condition_vars.get('experimenter', ''),
            instructions=self.condition_vars.get('instructions_condition', ''),
            search_radius=self.condition_vars.get('search_radius', ''),
            n_search_items=self.condition_vars.get('n_search_items', ''),
            pos=pos_to_str(self.pos),
            stims=pos_list_to_str(gabors.keys()),
        )

        for pos, grid_pos in zip(self.stim_positions, gabors.keys()):
            gabor = gabors[grid_pos]
            gabor.pos = pos
            gabor.draw()

        self.win.flip()
        grid_pos, gabor_pos, time = self.get_mouse_click(gabors)
        score = self.landscape.get_score(grid_pos)
        self.pos = grid_pos      # update current pos
        prev_score = self.score
        self.score += score      # update current score

        trial_data['selected'] = pos_to_str(grid_pos)
        trial_data['rt'] = time
        trial_data['score'] = score
        trial_data['total'] = self.score

        for gabor in gabors.values():
            gabor.draw()

        selected_label = self.label_gabor_score(score, gabor_pos, bold=True)
        self.draw_score(prev_score, score)

        if training:
            # Draw gabors again, this time with scores overlayed
            self.trial_header.text = self.texts['trial']['feedback']
            self.trial_header.draw()

            # Draw selected label as green unless another is higher score
            selected_label.color = 'green'
            for other_grid_pos, gabor in gabors.items():
                if grid_pos == other_grid_pos:
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

        else:
            selected_label.draw()
            self.win.flip()
            core.wait(self.feedback_duration)

        self.draw_score()
        self.win.flip()

        core.wait(self.iti)
        return trial_data

    def get_mouse_click(self, gabors):
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

    def write_trial(self, trial_data):
        trial_strings = []
        for col_name in DATA_COLUMNS:
            datum = trial_data.get(col_name, '')
            trial_strings.append(str(datum))
        self.write_line(trial_strings)

    def write_line(self, list_of_strings):
        self.output_file.write(','.join(list_of_strings)+'\n')

    def quit(self):
        core.quit()
        self.output_file.close()
