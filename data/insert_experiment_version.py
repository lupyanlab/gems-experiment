from pathlib import Path
import pandas

for filename in Path(".").glob("*.csv"):
    df = pandas.read_csv(filename)
    if "version" not in df:
        df.insert(4, "version", "1.1")
        df.to_csv(filename, index=False)
