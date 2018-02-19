from invoke import task
from gems import Experiment


@task
def show_texts(ctx, instructions_condition='orientation'):
    """Show the instructions for the experiment."""
    Experiment.win_size = (600 * 2, 400 * 2)
    experiment = Experiment(instructions_condition=instructions_condition)
    experiment.show_welcome()
    experiment.show_training()
    experiment.show_test()
    # experiment.show_break()
    # experiment.show_end()
    experiment.quit()


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
    trial_data = experiment.run_trial()
    print(trial_data)
    experiment.quit()


@task
def run_test_trials(ctx, n_test_trials=1):
    """Run test trials."""
    Experiment.win_size = (600 * 2, 400 * 2)
    experiment = Experiment(subj_id='pierce')
    experiment.run_test_trials(n_test_trials)


@task
def run_training_trials(ctx, n_training_trials=1):
    """Run training trials."""
    Experiment.win_size = (600 * 2, 400 * 2)
    experiment = Experiment(subj_id='pierce')
    experiment.run_training_trials(n_training_trials)
    experiment.quit()
