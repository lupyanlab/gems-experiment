#!/usr/bin/env python
import argparse
import gems

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', '-t', action='store_true')
    args = parser.parse_args()

    if args.test:
        gems.Experiment.win_size = (600 * 2.5, 400 * 2.5)

    experiment = gems.Experiment.from_gui('gui.yml')
    experiment.run()
