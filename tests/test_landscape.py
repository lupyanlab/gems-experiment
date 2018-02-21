from gems import Landscape, SimpleHill, StaticLandscape


def test_convert_landscape_to_tidy_data():
    landscape = Landscape(n_rows=2, n_cols=2, score_func=lambda (x,y): 1)
    tidy_data = landscape.to_tidy_data()
    assert len(tidy_data) == 4
    assert tidy_data.columns.tolist() == 'x y ori sf score'.split()

def test_get_score_on_simple_hill():
    simple_hill = SimpleHill(normalize=False, jitter=False)
    assert simple_hill.score((50, 50)) == 5000

def test_get_gabors_surrounding_grid_pos():
    landscape = Landscape(n_rows=3, n_cols=3, score_func=lambda (x,y): 1)
    neighbors = landscape.get_neighborhood((1, 1), radius=1)
    assert len(neighbors) == 9

def test_sample_neighborhood():
    landscape = Landscape(n_rows=10, n_cols=10, score_func=lambda (x,y): 1)
    sampled_neighbors = landscape.sample_neighborhood(9, (5, 5), 4)
    assert len(sampled_neighbors) == 9

def test_get_neighbors_ignorse_those_off_map():
    landscape = Landscape(n_rows=3, n_cols=3, score_func=lambda (x,y): 1)
    neighbors = landscape.get_neighborhood((0, 0), radius=1)
    assert len(neighbors) == 4
    assert set(neighbors) == set([(0,0), (0,1), (1,1), (1,0)])

def test_read_landscape_from_file():
    landscape = StaticLandscape('tests/test_landscapes/simple_landscape.csv')
    assert landscape.score((0, 0)) == 100

def test_read_landscape_from_name():
    landscape = StaticLandscape('SimpleHill')
    assert landscape.score((0, 0)) is not None
