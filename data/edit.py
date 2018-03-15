import re
from os import listdir
import pandas

re_subj_num = 'GEMS(\d+)\.csv'

for csv in listdir('.'):
    try:
        subj_num = int(re.findall(re_subj_num, csv)[0])
    except:
        print('skipping %s' % csv)
        continue

    if subj_num < 115:
        continue

    elif subj_num < 200:
        data = pandas.read_csv(csv)
        data.insert(7, 'start_pos_list_ix', 0)
        data.insert(8, 'start_pos_list', '0-0;0-0;0-0;0-0')
        data.to_csv(csv, index=False)

    elif subj_num in [201, 202]:
        data = pandas.read_csv(csv)
        data.insert(7, 'start_pos_list_ix', 1)
        data.insert(8, 'start_pos_list', '25-64;11-35;10-28;28-3')
        data.to_csv(csv, index=False)

    elif subj_num == 203:
        data = pandas.read_csv(csv)
        data.insert(7, 'start_pos_list_ix', 2)
        data.insert(8, 'start_pos_list', '28-29;36-13;68-56;33-8')
        data.to_csv(csv, index=False)
