from invoke import Collection

from . import landscape, experiment, subjects, figures

ns = Collection()
ns.add_collection(experiment, 'exp')
ns.add_collection(landscape, 'landscape')
ns.add_collection(subjects, 'subjs')
ns.add_collection(figures, 'fig')
