#!/usr/bin/env python
import os
import argparse
import gems


simulations_dir = "data/simulations"
if not os.path.isdir(simulations_dir):
    os.mkdir(simulations_dir)


def simulate_random(**kwargs):
    for seed in range(kwargs["seeds"]):
        output = os.path.join(simulations_dir, "random-seed-{seed}.csv".format(seed=seed))
        simulation = gems.RandomSimulation(seed=seed, output=output)
        simulation.run()


def simulate_optimal(**kwargs):
    pass


simulators = dict(random=simulate_random, optimal=simulate_optimal)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", "-t", choices=simulators.keys(), required=True)
    parser.add_argument("--seeds", "-s", type=int, default=1)
    args = parser.parse_args()
    simulator_fn = simulators[args.type]
    simulator_fn(**args.__dict__)
