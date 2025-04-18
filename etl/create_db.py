import pandas as pd
import numpy as np

from timescaledb_model import initial_markets_data
import re


def clean_numeric_column(series):
    return (
        series.astype(str)
        .str.replace(',', '.', regex=False)
        .str.replace(' ', '', regex=False)
        .replace('-', np.nan)  # important : gérer explicitement "-"
        .str.extract(r'([-+]?\d*\.?\d+)')[0]
        .astype(float)
    )



def create_db(df, df_bourso:pd.DataFrame, df_eronext:pd.DataFrame, db):

    df_markets = populate_markets()
    df_companies = populate_companies(df, df_markets)
    df_daystocks = populate_daystocks(df_eronext, df_companies)
    df_stocks = populate_stocks(df_bourso, df_companies)

    # Create the tables in the database
    db.df_write(df_companies, "companies")
    # db.df_write(df_markets, "markets")
    db.df_write(df_stocks, "stocks")
    db.df_write(df_daystocks, "daystocks")


    return None

def populate_companies(df, df_markets):
    df_companies = pd.DataFrame()

    df_companies["isin"] = df["isin"].values
    df_companies["name"] = df["name"].values

    # Merge df with df_markets on the 'prefix' and 'boursorama' columns, with explicit suffixes
    merged_df = df.merge(
        df_markets[['boursorama', 'id', 'name']],
        how='left',
        left_on='prefix',
        right_on='boursorama',
        suffixes=('_action', '_market')  # Explicit suffixes to avoid conflicts
    )

    # Extract the 'id' and 'name_market' columns from the merged dataframe
    df_companies["mid"] = merged_df["id"].fillna(-1).astype(int)  # Ensure 'mid' is an integer
    df_companies["symbol"] = df["symbol"].values
    df_companies["boursorama"] = df["boursorama"].values
    df_companies["id"] = np.arange(len(df_companies))

    df_companies["euronext"] = df["ticker"].values
    eligible_pea = ["Bourse de Milan", "Mercados Espanoles", "Amsterdam", "Paris", "Deutsche Borse", "Bruxelle"]

    # Use the 'name_market' column to determine eligibility for PEA
    df_companies["pea"] = merged_df["name_market"].apply(lambda name: name in eligible_pea if pd.notna(name) else False)

    df_companies["sector1"] = ""  # TODO
    df_companies["sector2"] = ""  # TODO
    df_companies["sector3"] = ""  # TODO

    # Drop duplicates based on all columns except 'id'
    df_companies = df_companies.loc[:, ~df_companies.columns.isin(['id'])].drop_duplicates().reset_index(drop=True)

    # Reassign unique IDs after dropping duplicates
    df_companies["id"] = np.arange(len(df_companies))

    return df_companies



def populate_markets():
    # Convert initial_markets_data to a DataFrame for easier manipulation
    initial_data = pd.DataFrame(
        initial_markets_data,
        columns=["id", "name", "alias", "boursorama", "euronext", "sws"]
    )

    # Create the markets DataFrame
    df_markets = pd.DataFrame()
    df_markets["id"] = initial_data["id"]
    df_markets["name"] = initial_data["name"]
    df_markets["alias"] = initial_data["alias"]

    # Map boursorama prefixes to the corresponding markets
    df_markets["boursorama"] = initial_data["boursorama"]

    # Map euronext tickers to the corresponding markets
    df_markets["euronext"] = np.nan

    # Fill the "sws" column with data from initial_markets_data
    df_markets["sws"] = initial_data["sws"]


    return df_markets

def populate_stocks(df_boursorama: pd.DataFrame, df_companies: pd.DataFrame):
    df_stocks = pd.DataFrame()

    # Reset index to avoid ambiguity with 'symbol', without adding the old index as a column
    df_boursorama = df_boursorama.reset_index(drop=True)
    df_companies = df_companies.reset_index(drop=True)

    # Merge df_boursorama with df_companies on the 'symbol' column
    merged_df = df_boursorama.merge(
        df_companies[['symbol', 'id']],
        how='left',
        left_on='symbol',
        right_on='symbol',
        suffixes=('', '_company')  # Avoid suffix conflicts
    )

    # Populate the stocks dataframe
    df_stocks["date"] = merged_df["date"]
    df_stocks["cid"] = merged_df["id"].fillna(-1).astype(int)  # Ensure 'cid' is an integer
    df_stocks["value"] = clean_numeric_column(merged_df["last"])
    df_stocks["volume"] = merged_df["volume"]

    return df_stocks

def populate_daystocks(df_euronext: pd.DataFrame, df_companies: pd.DataFrame):
    df_daystocks = pd.DataFrame()

    # Merge df_euronext with df_companies on the 'isin' column
    merged_df = df_euronext.merge(
        df_companies[['isin', 'id']],
        how='left',
        left_on='isin',
        right_on='isin',
        suffixes=('', '_company')  # Avoid suffix conflicts
    )

    # Populate the daystocks dataframe
    df_daystocks["date"] = merged_df["date"]
    df_daystocks["cid"] = merged_df["id"].fillna(-1).astype(int)  # Ensure 'cid' is an integer
    df_daystocks["open"] = merged_df["open"]
    df_daystocks["close"] = merged_df["close"]
    df_daystocks["high"] = merged_df["high"]
    df_daystocks["low"] = merged_df["low"]
    df_daystocks["volume"] = merged_df["volume"]
    df_daystocks["mean"] = (merged_df["high"] + merged_df["low"]) / 2
    df_daystocks["std"] = merged_df["high"] - merged_df["low"]

    for col in ["open", "close", "high", "low", "mean", "std", "volume"]:
        df_daystocks[col] = clean_numeric_column(df_daystocks[col])

    return df_daystocks