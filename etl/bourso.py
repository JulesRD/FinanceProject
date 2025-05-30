from mylogging import getLogger
import os
import pandas as pd
import datetime
import re


HOME = "/home/bourse/data/"
logger = getLogger(__name__)

import os
import pandas as pd
import datetime
import re
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor

# Regex optimisée pour extraire date + heure
_date_re = re.compile(r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}\.\d+)')

def extract_date_hours(path):
    file_name = path.split('/')[-1]
    match = _date_re.search(file_name)
    if not match:
        return None

    date_str = match.group(1)
    time_str = match.group(2)
    return datetime.datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M:%S.%f')


def extract_symbole(df):
    df["boursorama"] = df["symbol"].str[:3]
    df["symbol"] = df["symbol"].str[3:]


def list_all_file():
    list_path = []
    for dir_date in os.listdir(HOME + "boursorama"):
        for file_name in os.listdir(HOME + "boursorama/" + dir_date):
            full_path = os.path.join(HOME, "boursorama", dir_date, file_name)
            list_path.append(full_path)
    return list_path
def delete_volument_equal_zero(df):
    df = df[df['volume'] != 0]
    return df
def delete_symbole_ending_with_NV(df):
    df = df[~df['symbol'].str.endswith('NV')]
    return df
def get_df(list_path, start = 0, end = 10000):
    df_list = []
    for path in list_path:
        df_tmp = pd.read_pickle(path)
        df_tmp['date'] = extract_date_hours(path)
        df_list.append(df_tmp)
        start += 1
        if start >= end:
            break
    df = pd.concat(df_list, ignore_index=True)
    extract_symbole(df)
    df = delete_symbole_ending_with_NV(df)
    df = delete_volument_equal_zero(df)
    logger.info("All files loaded")
    return df


