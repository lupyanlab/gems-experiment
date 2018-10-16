#!/usr/bin/env python
import argparse
import gems


def simulate_random(**kwargs):
    pass

def simulate_optimal(**kwargs):
    pass


simulators = dict(random=simulate_random, optimal=simulate_optimal)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", "-t", choices=["random", "optimal"], required=True)
    args = parser.parse_args()
    simulator = simulators[args.type]
    simulator(**args.__dict__)
