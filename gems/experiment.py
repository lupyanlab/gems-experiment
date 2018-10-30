import string
import subprocess
import webbrowser
from os import path

import yaml

import pandas
from psychopy import visual, core, event

from . import landscape
from .config import pkg_root, data_columns, INSTRUCTIONS_DIR
from .display import create_radial_positions, create_line_positions
from .util import pos_to_str, pos_list_to_str
from .subj_info import get_subj_info, make_output_filepath, check_output_filepath, convert_condition_vars, verify_subj_info
from .inherited_instructions import load_ancestor_instructions


EXPERIMENT_VERSION = '1.3'


class Experiment(object):
    # Responses ----
    response_keys = ['space']
    response_text = 'Press SPACEBAR to continue.'

    # Wait times in seconds ----
    duration_fix = 1
    duration_feedback = 2
    duration_iti = 1.0
    duration_break_minimum = 5

    # Window settings ----
    win_size = None  # no size means full screen
    win_color = (.6, .6, .6)

    # Stimulus presentation ----
    gabor_size = 120    # in pix
    n_gabors = 6        # gabors per trial
    gabor_y_pos = 75
    prev_gabor_y_pos = -175
    stim_radius = 200   # pix between fix and center of grating stim

    # Players ----
    total_score = 0
    sight_radius = 10  # range of sight on the grid in the landscape
    pos = (0, 0)       # initial grid position on the landscape
    n_trials_per_block = 80

    # Defaults ----
    text_kwargs = dict(font='Consolas', color='black', pos=(0,50))
    grating_stim_kwargs = dict(size=gabor_size)

    @classmethod
    def from_gui(cls, gui_yaml):
        """Create an experiment after obtaining condition vars from a GUI."""
        subj_info = get_subj_info(gui_yaml,
            version=EXPERIMENT_VERSION,
            check_exists=check_output_filepath,
            verify=verify_subj_info,
            save_order=True)
        subj_info = convert_condition_vars(subj_info)

        return cls(**subj_info)

    def __init__(self, **condition_vars):
        self.condition_vars = condition_vars
        self.texts = yaml.load(open(path.join(pkg_root, 'texts.yaml')))
        self._cache = {}
        self.data_columns = data_columns

        self.stim_positions = \
            create_line_positions(self.n_gabors, screen_width=self.win.size[0]-(3*self.gabor_size), y_pos=self.gabor_y_pos)

        self.trial_header = self.make_text('',
            draw=False,
            pos=(0, self.stim_radius*1.25),
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

        self.prev_gem_text = self.make_text('Here is the gem you selected last.', draw=False, pos=(0,self.prev_gabor_y_pos-self.gabor_size))
        self.mouse = event.Mouse()
        self.exp_timer = core.Clock()

        try:
            self.prefilled_survey_url = self.get_text('survey').format(**self.condition_vars)
        except KeyError:
            self.prefilled_survey_url = self.get_text('survey').format(subj_id='', computer='')

        self.use_landscape('SimpleHill')

    def run(self):
        self.exp_timer.reset()
        self.show_welcome()
        self.show_example_trial()
        if self.get_var('generation') > 1:
            self.show_inherited_instructions()
        self.show_foreshadow()
        self.show_pre_test()
        self.run_test_trials()
        self.show_end()
        self.quit()

    def show_welcome(self, save_screenshot=False):
        self.make_title(self.get_text('welcome_title'))

        # Show welcome text conditional on generation
        generation = self.get_var('generation')
        assert generation >= 1, "generation was not 1 or greater"
        if generation == 1:
            generation_instructions = self.get_text("generation_instructions")["generation_1"]
        else:
            generation_instructions = self.get_text("generation_instructions")["generation_N"]
        welcome_text = self.get_text('welcome_text').format(
            generation_instructions=generation_instructions)
        self.make_text(welcome_text)

        self.make_explorer()

        selected_grid_positions = [(30, 30), (50, 50), (70, 70)]
        stim_positions = [(-200, -150), (0, -150), (200, -150)]
        for grid_pos, gabor_pos in zip(selected_grid_positions, stim_positions):
            gabor = self.landscape.get_grating_stim(grid_pos)
            gabor.pos = gabor_pos
            gabor.draw()

        self.win.flip()
        event.waitKeys(keyList=self.response_keys)

    def show_example_trial(self):
        gabors = self.sample_gabors()
        self.make_text(
			self.get_text('example_trial_title'),
			pos=(0, 2*self.stim_radius),
            alignVert='top',
            height=30,
            wrapWidth=self.win.size[0]
		)
        self.make_text(self.get_text("example_trial"), pos=(0,250))
        self.trial_header.draw()
        # self.fixation.draw()
        for gabor in gabors.values():
            gabor.draw()
        self.win.flip()
        event.waitKeys(['space'])

    def show_inherited_instructions(self):
        self.make_title(self.get_text('ancestor_instructions_title'))
        inherited = load_ancestor_instructions(self.get_var('inherit_from'))
        body = self.get_text("ancestor_instructions").format(ancestor_response=inherited)
        self.make_text(body)
        self.win.flip()
        event.waitKeys(['space'])

    def show_foreshadow(self):
        self.make_title(self.get_text("foreshadow_title"))
        self.make_text(self.get_text("foreshadow"))
        self.make_explorer()
        self.win.flip()
        event.waitKeys(['space'])

    def show_pre_test(self):
        self.make_title(self.get_text('pre_test_title'))
        self.make_text(self.get_text("pre_test"))
        self.make_explorer()
        self.win.flip()
        event.waitKeys(['space'])

    def record_instructions(self):
        instructions = self.get_instructions()
        instructions_path = path.join(INSTRUCTIONS_DIR, '{}.txt'.format(self.get_var('subj_id')))
        open(instructions_path, 'w').write(instructions)

    def get_instructions(self):
        typing = True
        is_cap = False
        message = ''

        texts = self.get_text("instructions")
        title = self.make_title(texts["title"])
        descr = self.make_text(texts["descr"], pos=(0, 170))
        text_box = self.make_text('_', pos=(-250, 0), wrapWidth=500, alignHoriz='left')
        error = self.make_text("", pos=(0, -180), color="red")

        punct = dict(
            period = '.',
            comma = ',',
            apostrophe = "'",
        )

        while typing:
            keys = event.getKeys()
            if keys:
                key = keys[0]

                if key == 'escape':  # bit.ly/pyglet-key-names
                    if len(message) < 100:
                        error.setText(texts["too_short"])
                        continue
                    else:
                        typing = False
                        continue
                elif key in ['lshift', 'rshift']:
                    is_cap = True
                    continue
                elif key == 'space':
                    key = ' '
                elif key == 'backspace':
                    message = message[:-1]
                    key = ''
                elif key in punct:
                    key = punct[key]
                elif key not in string.letters and key not in string.digits:
                    continue

                if is_cap:
                    key = key.upper()
                    is_cap = False

                error.setText("")
                message += key
                text_box.setText(message + "_")

            title.draw()
            descr.draw()
            text_box.draw()
            error.draw()
            self.win.flip()

        return message

    def run_test_trials(self):

        self.use_landscape(self.get_var("landscape"))

        for landscape_ix, start_pos in enumerate([(0,0), (0,0)]):
            if landscape_ix == 1:
                self.record_instructions()
                self.show_break()

            self.pos = start_pos
            self.total_score = self.landscape.score(start_pos)

            block_data = dict(
                generation=self.get_var('generation'),
                inherit_from=self.get_var('inherit_from'),
                block_ix=landscape_ix+1,
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
        webbrowser.open(self.prefilled_survey_url)

    def sample_gabors(self):
        """Sample gabors in a certain radius and assign them positions on the screen.

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
            version=self.get_var('version'),
            sight_radius = self.sight_radius,
            n_gabors = self.n_gabors,
            pos = pos_to_str(self.pos)
        )
        trial_data.update(kwargs)
        return trial_data

    def run_trial(self, trial=0, feedback='training', landscape_title='', save_screenshot=False):
        gabors = self.sample_gabors()
        trial_data = self.make_trial_data(feedback=feedback,
                                          stims=pos_list_to_str(gabors.keys()),
                                          trial=trial)

        self.landscape_title.text = landscape_title

        # Begin trial presentation ----
        #self.fixation.draw()
        prev_gem = None
        self.landscape_title.draw()
        if trial > 0:
            self.prev_gem_text.draw()
            prev_gem = self.landscape.get_grating_stim(self.pos)
            prev_gem.pos = (0, self.prev_gabor_y_pos)
            prev_gem.draw()
            self.draw_score()
            self.trial_header.text = self.get_trial_text('instructions_N')
        else:
            # first trial in block
            self.trial_header.text = self.get_trial_text('instructions_0')
        self.win.flip()
        core.wait(self.duration_fix)

        self.trial_header.draw()
        self.landscape_title.draw()
        if trial > 0:
            prev_gem.draw()
            self.prev_gem_text.draw()
            self.draw_score()
        # self.fixation.draw()
        for gabor in gabors.values():
            gabor.draw()
        self.win.flip()
        if save_screenshot:
            self.save_screenshot('{}_trial.png'.format(feedback))

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
            self.give_training_feedback(gabors, prev_grid_pos, grid_pos, trial, save_screenshot=save_screenshot)
        elif feedback == 'selected':
            self.give_selected_feedback(gabors, prev_grid_pos, grid_pos, trial, save_screenshot=save_screenshot)

        trial_data['selected'] = pos_to_str(grid_pos)
        trial_data['rt'] = round(time, 2)
        trial_data['score'] = new_gem_score
        trial_data['delta'] = diff_from_prev_gem

        self.landscape_title.draw()
        self.draw_score()
        self.win.flip()
        core.wait(self.duration_iti)

        return trial_data

    def give_training_feedback(self, gabors, prev_grid_pos, selected_grid_pos, trial, save_screenshot=False):
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

        picked_correctly = (selected_grid_pos in most_valuable_grid_pos_list)
        if picked_correctly:
            # Participant picked the most valuable on this trial.
            self.trial_header.text = self.get_trial_text('training_correct_feedback')
            self.trial_header.color = 'green'
        else:
            # Participant did not pick the most valuable.
            # Make them pick the most valuable.
            self.trial_header.text = self.get_trial_text('training_incorrect_feedback')

        self.landscape_title.draw()
        self.trial_header.draw()
        if trial == 0:
            prev_score = None
        self.draw_score(prev_score)
        highlight.draw()
        self.win.flip()
        if save_screenshot:
            self.save_screenshot('training_trial_feedback.png')
        self.get_clicked_gabor(gabors, most_valuable_grid_pos_list)

        self.trial_header.color = 'black'  # reset

    def give_selected_feedback(self, gabors, prev_grid_pos, selected_grid_pos, trial, save_screenshot=False):
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
        if save_screenshot:
            self.save_screenshot('test_trial_feedback.png')
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
        event.clearEvents(eventType='keyboard')
        while waiting_for_response:
            core.wait(0.01)
            (left_click, _, _), (time, _, _) = self.mouse.getPressed(getTime=True)
            if left_click:
                pos = self.mouse.getPos()
                for grid_pos, gabor in targets.items():
                    if gabor.contains(pos):
                        waiting_for_response = False
                        break

            keys = event.getKeys(keyList=['q'])
            if keys:
                self.show_end()
                self.quit()

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
        explorer = visual.ImageStim(self.win, explorer_png, pos=(0, -325), size=200)
        if draw:
            explorer.draw()
        return explorer

    @property
    def output(self):
        if 'output' in self._cache:
            return self._cache['output']

        self._cache['output'] = open(self.condition_vars['filename'], 'w', 1)

        # Write CSV header
        self.write_line(self.data_columns)

        return self._cache['output']

    def write_trial(self, trial_data):
        trial_strings = []
        for col_name in self.data_columns:
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

    def save_screenshot(self, name):
        self.win.getMovieFrame()
        self.win.saveMovieFrames(name)
