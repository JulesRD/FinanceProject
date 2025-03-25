import pandas as pd
import numpy as np
import os

import datetime
HOME = "/home/bourse/data/"

def extract_date_hours(path):
    file_name = path.split('/')[-1]  # Extract the file name
    date_str, time_str = file_name.split(' ')[1:3]  # Extract date and time parts
    time_str = ".".join(time_str.split('.')[0:2])
    date_time_str = f"{date_str} {time_str}"
    date_time = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')
    return date_time

def merge_df(file_path, df):
    df_tmp = pd.read_pickle(
    file_path,
    )
    # df.reset_index(drop=True, inplace=True)
    df_tmp['date'] = extract_date_hours(file_path)
    return pd.concat([df, df_tmp])
  
def get_df(num_files=100):
    df = pd.DataFrame()
    dir = os.listdir(HOME + "boursorama")
    i = 0
    for dir_date in dir :
        list_file_path = os.listdir(HOME + "boursorama/" + dir_date)
        for file_path in list_file_path :
            df = merge_df(HOME + "boursorama/" + dir_date + "/" + file_path, df)
            if (i == num_files) :
                break
            i+=1
        break
    return df