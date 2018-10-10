import pandas
import shutil

items = [
    ("GEMS137a", "GEMS144"),
    ("GEMS138a", "GEMS145"),
    ("GEMS141a", "GEMS146"),
    ("GEMS142a", "GEMS147"),
]

for old, new in items:
    df = pandas.read_csv(old + ".csv")
    df["subj_id"] = new
    df.to_csv(new + ".csv", index=False)

    shutil.copy("instructions/%s.txt" % old, "instructions/%s.txt" % new)
