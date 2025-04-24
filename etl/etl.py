import pandas as pd
import numpy as np
import sklearn
import glob
import time
import re
import timescaledb_model as tsdb
from mylogging import getLogger


from bourso import get_df as get_df_boursorama
from bourso import list_all_file
from euronext import get_df as get_df_euronext
from create_db import create_db
from merger_df import merge_dataset

TSDB = tsdb.TimescaleStockMarketModel
HOME = "/home/bourse/data/"   # we expect subdirectories boursorama and euronext


logger = getLogger(__name__)
#=================================================
# Extract, Transform and Load data in the database
#=================================================

#
# private functions
# 

REMOVE_ALL = False
if REMOVE_ALL:
    df_eronext = get_df_euronext(n=9999999999)
    db = tsdb.TimescaleStockMarketModel('bourse', 'ricou', 'db', 'monmdp', remove_all=REMOVE_ALL)
    list_path = list_all_file()
    start = 0
    end = 10000
    df_companies, df_markets = None, None
    while start < len(list_path):
        logger.info("start: %s, end: %s", start, end)
        tps_bourso = time.time()
        df_bourso = get_df_boursorama(list_path, start = start, end = end)
        tps_bourso = time.time() - tps_bourso
        tps_merge = time.time()
        df = merge_dataset(df_bourso, df_eronext, delete_name_alone=True)
        tps_merge = time.time() - tps_merge

        tps_database = time.time()
        df_markets, df_companies = create_db(df, df_bourso, df_eronext, db, only_stocks = (start!=0), df_companies=df_companies, df_markets=df_markets)
        tps_database = time.time() - tps_database
        logger.info("tps_bourso: %s, tps_merge: %s, tps_database: %s", tps_bourso, tps_merge, tps_database)
        logger.info("database inserted")
        start = end
        end += 10000
        del df_bourso
        del df
        df_bourso = None
        df = None
else:
    db = tsdb.TimescaleStockMarketModel('bourse', 'ricou', 'db', 'monmdp', remove_all=REMOVE_ALL)


logger.info("Start pushing stocks into database")
# df_stocks = pd.read_csv("/tmp/stocks.csv.gz", compression="gzip")
# db.df_write(df_stocks, "stocks")
# logger.info("End pushing stocks into database")

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
