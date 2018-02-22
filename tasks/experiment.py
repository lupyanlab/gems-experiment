from invoke import task
import gems
from gems import Experiment


@task
def show_texts(ctx, instructions_condition='orientation'):
    """Show the instructions for the experiment."""
    Experiment.win_size = (600 * 2, 400 * 2)
    experiment = Experiment(instructions_condition=instructions_condition)
    experiment.use_landscape('SimpleHill')
    experiment.show_welcome()
    experiment.show_training()
    experiment.show_test()
    experiment.show_break()
    # experiment.show_end()
    # experiment.quit()


@task
def gui(ctx):
    """Open the subject info GUI and print the results."""
    experiment = Experiment.from_gui('gui.yml')
    print(experiment.condition_vars)


@task
def run_trial(ctx):
    """Run a single trial."""
    Experiment.win_size = (600 * 2, 400 * 2)
    experiment = Experiment()
    experiment.use_landscape('SimpleHill')
    trial_data = experiment.run_trial()
    print(trial_data)
    experiment.quit()


@task
def run_test_trials(ctx, n_test_trials=5, instructions_condition='orientation'):
    """Run test trials."""
    Experiment.win_size = (600 * 2, 400 * 2)
    Experiment.n_trials_per_block = n_test_trials
    output = 'test-{}.csv'.format(instructions_condition)
    experiment = Experiment(subj_id='pierce', instructions_condition=instructions_condition, filename=output, starting_positions=[(0,0), ])
    experiment.use_landscape('SimpleHill')
    experiment.run_test_trials()
    experiment.quit()


@task
def run_training_trials(ctx, n_training_trials=5, instructions_condition='orientation'):
    """Run training trials."""
    Experiment.win_size = (600 * 2, 400 * 2)
    Experiment.n_training_trials = n_training_trials
    output = 'training-{}.csv'.format(instructions_condition)
    experiment = Experiment(subj_id='pierce', instructions_condition=instructions_condition, filename=output)
    experiment.use_landscape('SimpleHill')
    experiment.run_training_trials()
    experiment.quit()
