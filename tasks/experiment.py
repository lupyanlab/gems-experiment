from os import path, mkdir, listdir, remove
from invoke import task
import yaml
import pandas
import gems
from gems import Experiment

@task
def label_pos_lists(ctx):
    pos_lists_filename = 'pos-lists.csv'

    data_dir = 'data'
    data_filepaths = ['%s/%s' % (data_dir, data_file)
                      for data_file in listdir(data_dir)]

    if not path.exists(pos_lists_filename):
        with open(pos_lists_filename, 'w') as f:
            f.write('0-0;0-0;0-0;0-0\n')

    prev_pos_list_strs = [pos_list_str.strip()
                          for pos_list_str in open(pos_lists_filename)]

    with open('pos-lists.csv', 'w') as appender:
        for path_name in sorted(data_filepaths):
            data = pandas.read_csv(path_name)
            if 'start_pos_list_ix' not in data:
                continue

            if data.start_pos_list_ix.iloc[0] != 0:
                continue

            midway_positions = data.ix[
                (data.landscape_ix > 0) & (data.trial == 20),
                'pos'].tolist()

            # expecting four positions
            if len(midway_positions) != 4:
                continue

            pos_list_str = ';'.join(midway_positions)
            if pos_list_str not in prev_pos_list_strs:
                appender.write('{subj_id},{pos_list_str}\n'.format(
                    subj_id=data.subj_id.iloc[0], pos_list_str=pos_list_str))

@task
def write_pos_lists(ctx, clear=False):
    """Write pos at trial 20 to text file."""
    pos_lists_filename = 'pos-lists.txt'

    data_dir = 'data'
    data_filepaths = ['%s/%s' % (data_dir, data_file)
                      for data_file in listdir(data_dir)]

    if clear:
        remove(pos_lists_filename)

    if not path.exists(pos_lists_filename):
        with open(pos_lists_filename, 'w') as f:
            f.write('0-0;0-0;0-0;0-0\n')

    prev_pos_list_strs = [pos_list_str.strip()
                          for pos_list_str in open(pos_lists_filename)]

    with open('pos-lists.txt', 'a') as appender:
        for path_name in sorted(data_filepaths):
            data = pandas.read_csv(path_name)
            if 'start_pos_list_ix' not in data:
                continue

            if data.start_pos_list_ix.iloc[0] != 0:
                continue

            midway_positions = data.ix[
                (data.landscape_ix > 0) & (data.trial == 20),
                'pos'].tolist()

            # expecting four positions
            if len(midway_positions) != 4:
                continue

            pos_list_str = ';'.join(midway_positions)
            if pos_list_str not in prev_pos_list_strs:
                appender.write(pos_list_str+'\n')

@task
def show_texts(ctx, instructions_condition='orientation'):
    """Show the instructions for the experiment."""
    Experiment.win_size = (600 * 2.5, 400 * 2.5)
    experiment = Experiment(instructions_condition=instructions_condition)
    experiment.use_landscape('SimpleHill')
    experiment.show_welcome()
    experiment.show_training()
    experiment.show_test()
    experiment.show_break()
    experiment.show_end()
    # experiment.quit()


@task
def show_training(ctx, save_screenshots=False, move_to_r_pkg=False):
    """Show both instruction types."""
    Experiment.win_size = (600 * 2.5, 400 * 2.5)
    experiment = Experiment()
    experiment.use_landscape('SimpleHill')

    screenshots_dir = 'gems/screenshots'
    if move_to_r_pkg:
        screenshots_dir = '../data/inst/extdata'

    if not path.isdir(screenshots_dir):
        mkdir(screenshots_dir)

    experiment.condition_vars['instructions_condition'] = 'orientation'
    experiment.show_welcome(save_screenshot=save_screenshots)
    experiment.show_training(save_screenshot=save_screenshots)

    experiment.condition_vars['instructions_condition'] = 'spatial_frequency'
    experiment.show_welcome(save_screenshot=save_screenshots)
    experiment.show_training(save_screenshot=save_screenshots)

    if save_screenshots:
        ctx.run('mv ./*.png {}'.format(screenshots_dir), echo=True)

@task
def screenshot_training_trials(ctx):
    Experiment.win_size = (600 * 2.5, 400 * 2.5)
    experiment = Experiment()
    experiment.use_landscape('OrientationBias')
    experiment.pos = (5,5)
    experiment.total_score = experiment.landscape.score(experiment.pos)
    experiment.run_trial(trial=1, feedback='training', landscape_title='Training Quarry', save_screenshot=True)
    experiment.run_trial(trial=1, feedback='selected', landscape_title='Quarry 1', save_screenshot=True)


@task
def show_survey(ctx):
    Experiment.win_size = (600 * 2.5, 400 * 2.5)
    experiment = Experiment(subj_id='GEMS100', computer='LL-Kramer')
    experiment.show_end()


@task
def gui(ctx):
    """Open the subject info GUI and print the results."""
    experiment = Experiment.from_gui('gui.yml')
    print(experiment.condition_vars)


@task
def run_trial(ctx):
    """Run a single trial."""
    Experiment.win_size = (600 * 2.5, 400 * 2.5)
    experiment = Experiment()
    experiment.use_landscape('SimpleHill')
    trial_data = experiment.run_trial()
    print(trial_data)
    experiment.quit()


@task
def run_test_trials(ctx, n_test_trials=5, instructions_condition='orientation'):
    """Run test trials."""
    Experiment.win_size = (600 * 2.5, 400 * 2.5)
    Experiment.n_trials_per_block = n_test_trials
    output = 'test-{}.csv'.format(instructions_condition)

    starting_positions = gems.util.get_pos_list_from_ix(10)
    experiment = Experiment(subj_id='pierce', instructions_condition=instructions_condition, filename=output, starting_positions=starting_positions[:1])
    experiment.use_landscape('SimpleHill')
    experiment.run_test_trials()
    experiment.quit()


@task
def run_training_trials(ctx, n_training_trials=5, instructions_condition='orientation'):
    """Run training trials."""
    Experiment.win_size = (600 * 2.5, 400 * 2.5)
    Experiment.n_training_trials = n_training_trials
    output = 'training-{}.csv'.format(instructions_condition)
    experiment = Experiment(subj_id='pierce', instructions_condition=instructions_condition, filename=output)
    experiment.use_landscape('SimpleHill')
    experiment.run_training_trials()
    experiment.quit()
