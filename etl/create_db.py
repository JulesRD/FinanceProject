import pandas as pd
import numpy as np

def create_db(df_bourso:pd.DataFrame, df_eronext:pd.DataFrame, db):
    print("TODO: create database")

    return None

def populate_companies(df_bourso:pd.DataFrame, df_eronext:pd.DataFrame, db):
    print("TODO: populate companies")

    df_companies = df_bourso.copy()
    # fill with nan
    
    df_companies["isin"] = np.nan
    df_companies["boursorama"] = df_companies["symbol"]
    df_companies["symbol"].apply(lambda x: x[3: len(x)])
    df_companies["mid"] = np.nan # TODO
    df_companies["euronext"] = np.nan # TODO
    df_companies["pea"] = np.nan # TODO

    df_companies["sector1"] = np.nan # TODO
    df_companies["sector2"] = np.nan # TODO
    df_companies["sector3"] = np.nan # TODO

    db.df_write(df_companies, "companies")

    return None

def populate_markets(df_bourso:pd.DataFrame, df_eronext:pd.DataFrame, db):

    return None

def populate_stocks(df_bourso:pd.DataFrame, df_eronext:pd.DataFrame, db):

    return None

def populate_daystocks(df_bourso:pd.DataFrame, df_eronext:pd.DataFrame, db):

    return None