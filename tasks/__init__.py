from invoke import Collection

from . import landscape, experiment, subjects

ns = Collection()
ns.add_collection(experiment, 'exp')
ns.add_collection(landscape, 'landscape')
ns.add_collection(subjects, 'subjs')
