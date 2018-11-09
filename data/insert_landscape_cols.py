import re
import os
import pandas

data_files = [d for d in os.listdir(".") if d.startswith("GEMS")]

for f in data_files:
    subj_n = int(re.findall(r'\d+', f)[0])

    landscape_ix = 1
    landscape_name = "SimpleHill"
    if subj_n >= 259:
        landscape_ix = 2
        landscape_name = "Orientation"
    df = pandas.read_csv(f)
    df['landscape_name'] = landscape_name
    df['landscape_ix'] = landscape_ix
    df.to_csv(f, index=False)
