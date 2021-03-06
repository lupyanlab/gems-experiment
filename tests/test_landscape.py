from gems import Landscape, SimpleHill


def test_convert_landscape_to_tidy_data():
    landscape = Landscape(n_rows=2, n_cols=2, score_func=lambda (x,y): 1)
    tidy_data = landscape.to_tidy_data()
    assert len(tidy_data) == 4
    assert tidy_data.columns.tolist() == 'x y ori sf score'.split()

def test_get_score_on_simple_hill():
    simple_hill = SimpleHill(normalize=False)
    assert simple_hill.score((50, 50)) == 5000

def test_get_gabors_surrounding_grid_pos():
    landscape = Landscape(n_rows=3, n_cols=3, score_func=lambda (x,y): 1)
    neighbors = landscape.get_neighborhood((1, 1), radius=1)
    assert len(neighbors) == 5

def test_sample_neighborhood():
    landscape = Landscape(n_rows=10, n_cols=10, score_func=lambda (x,y): 1)
    sampled_neighbors = landscape.sample_neighborhood(9, (5, 5), 4)
    assert len(sampled_neighbors) == 9

def test_sample_neighborhood_circular():
    landscape = Landscape(n_rows=11, n_cols=11, score_func=lambda (x,y): 1)
    sampled_neighbors = landscape.get_neighborhood((5, 5), 5)
    assert (0, 0) not in sampled_neighbors
    assert (11, 11) not in sampled_neighbors
    assert (0, 11) not in sampled_neighbors
    assert (11, 0) not in sampled_neighbors

def test_get_neighbors_ignore_those_off_map():
    landscape = Landscape(n_rows=3, n_cols=3, score_func=lambda (x,y): 1)
    neighbors = landscape.get_neighborhood((0, 0), radius=1)
    assert len(neighbors) == 3
    assert set(neighbors) == set([(0,0), (0,1), (1,0)])
