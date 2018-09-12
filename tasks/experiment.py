from os import path, mkdir, listdir, remove
from invoke import task
import yaml
import pandas
import gems
from gems import Experiment


@task
def show_texts(ctx, generation=1):
    """Show the instructions for the experiment."""
    Experiment.win_size = (600 * 2.5, 400 * 2.5)
    experiment = Experiment(generation=generation)
    experiment.use_landscape('SimpleHill')
    experiment.show_welcome()
    # experiment.show_training()
    # experiment.show_test()
    # experiment.show_break()
    # experiment.show_end()
    # experiment.quit()


@task
def get_instructions(ctx):
    """Get instructions for the next generation."""
    Experiment.win_size = (600 * 2.5, 400 * 2.5)
    experiment = Experiment(subj_id='GEMS100')
    instructions = experiment.get_instructions()
    print(instructions)


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
