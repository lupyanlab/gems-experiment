import numpy

from gems.experiment import *
from gems.config import simulation_data_columns

class Simulation(Experiment):
    def __init__(self, seed, output):
        self.seed = seed
        self.random = numpy.random.RandomState(seed)

        self.condition_vars = dict(filename=output)
        self._cache = {}
        self.use_landscape('SimpleHill')
        self.data_columns = simulation_data_columns

    def run(self):
        self.pos = (0, 0)
        self.total_score = self.landscape.score(self.pos)

        block_data = dict(
            landscape_name=self.landscape.__class__.__name__,
            starting_pos=pos_to_str(self.pos),
            starting_score=self.total_score,
            block_ix=1
        )

        for trial in range(self.n_trials_per_block):
            trial_data = self.run_trial()
            trial_data["trial"] = trial
            trial_data.update(block_data)
            self.write_trial(trial_data)

    def run_trial(self):
        gabors = self.landscape.sample_neighborhood(self.n_gabors, self.pos, self.sight_radius)
        grid_pos = self.simulate_choice(gabors)

        # Compare selected gem to prev trial gem
        prev_gem_score = self.landscape.score(self.pos)
        new_gem_score = self.landscape.score(grid_pos)
        diff_from_prev_gem = new_gem_score - prev_gem_score

        prev_grid_pos = self.pos
        self.pos = grid_pos               # move to new pos
        self.total_score = new_gem_score  # update total score

        trial_data = self.make_trial_data(
            pos=pos_to_str(prev_grid_pos),
            stims=pos_list_to_str(gabors),
            selected=pos_to_str(grid_pos),
            score=new_gem_score,
            delta=diff_from_prev_gem,
        )
        return trial_data

    def make_trial_data(self, **kwargs):
        trial_data = dict(
            subj_id = "random_robot_{}".format(self.seed),
            simulation_type = self.simulation_type,
            sight_radius = self.sight_radius,
            n_gabors = self.n_gabors,
            pos = pos_to_str(self.pos)
        )
        trial_data.update(kwargs)
        return trial_data


    def simulate_choice(self, gabors):
        raise NotImplementedError()

class RandomSimulation(Simulation):
    simulation_type = "random"
    def simulate_choice(self, gabors):
        return gabors[self.random.choice(range(len(gabors)))]

class OptimalSimulation(Simulation):
    simulation_type = "optimal"
    def simulate_choice(self, gabors):
        best_gem = gabors[0]
        best_score = self.landscape.get_score(gabors[0])
        for pos in sorted(gabors[1:]):
            cur_score = self.landscape.get_score(pos)
            if cur_score > best_score:
                best_gem = pos
                best_score = cur_score
        return best_gem
