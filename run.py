#!/usr/bin/env python
import gems

if __name__ == '__main__':
    experiment = gems.Experiment.from_gui('gui.yml')
    experiment.run()
