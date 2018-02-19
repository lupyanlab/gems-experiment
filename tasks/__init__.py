from invoke import Collection

from . import landscape, experiment

ns = Collection()
ns.add_collection(experiment, 'exp')
ns.add_collection(landscape, 'landscape')
