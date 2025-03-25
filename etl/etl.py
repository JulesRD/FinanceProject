import pandas as pd
import numpy as np
import sklearn
import glob
import time
import re
import timescaledb_model as tsdb

from bourso import get_df as get_df_boursorama
from euronext import get_df as get_df_euronext
from create_db import create_db

TSDB = tsdb.TimescaleStockMarketModel
HOME = "/home/bourse/data/"   # we expect subdirectories boursorama and euronext

#=================================================
# Extract, Transform and Load data in the database
#=================================================

#
# private functions
# 
df_bourso = get_df_boursorama(num_files=100)
# df_eronext = get_df_euronext(n=100)

# database = create_db(df_bourso, df_eronext, db)
#
# decorator
# 

def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} run in {(end_time - start_time):.2f} seconds.")
        return result

    return wrapper

#
# public functions
# 

@timer_decorator
def store_files(start:str, end:str, website:str, db:TSDB):
    ...


if __name__ == '__main__':
    print("Go Extract Transform and Load")
    pd.set_option('display.max_columns', None)  # usefull for dedugging
    db = tsdb.TimescaleStockMarketModel('bourse', 'ricou', 'db', 'monmdp')        # inside docker
    #db = tsdb.TimescaleStockMarketModel('bourse', 'ricou', 'localhost', 'monmdp') # outside docker
    store_files("2020-01-01", "2020-02-01", "euronext", db) # one month to test
    print("Done Extract Transform and Load")
