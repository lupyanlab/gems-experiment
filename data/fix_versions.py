from pathlib import Path
import pandas
import re

for path in Path(".").glob("*.csv"):
    subj = pandas.read_csv(path)
    subj_num = int(re.findall("\d+", str(path))[0])

    if subj_num >= 234 and subj_num <= 257:
        print(f"subj {subj_num}, version: {subj.version.unique()[0]}, should be v1.3")
        subj["version"] = 1.3
    elif subj_num >= 237 and subj_num <= 282:
        print(f"subj {subj_num}, version: {subj.version.unique()[0]}, should be v1.3")
        subj["version"] = 1.3
    elif subj_num >= 283:
        subj["version"] = 1.5
        print(f"subj {subj_num}, version: {subj.version.unique()[0]}, should be v1.5")
    else:
        continue
    subj.to_csv(path, index=False)
