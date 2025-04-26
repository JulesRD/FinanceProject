import pandas as pd
import numpy as np

from timescaledb_model import initial_markets_data
import re

from mylogging import getLogger
from time import time
logger = getLogger(__name__)
import re

def clean_numeric_column(series):
    # Utilise une regex unique pour extraire les nombres, après un pré-nettoyage vectorisé
    cleaned = (
        series.astype(str)
        .str.replace(r'[ ,]', '', regex=True)  # supprime espaces et virgules en une passe
        .replace('-', np.nan)  # attention : ça marche si "-" est toute la valeur
        .str.extract(r'([-+]?\d*\.?\d+)')[0]
    )
    return pd.to_numeric(cleaned, errors='coerce')



def create_db(df, df_bourso:pd.DataFrame, df_eronext:pd.DataFrame, db, only_stocks=False, df_companies=None, df_markets=None):
    if df_companies is None:
        logger.info("populate markets and companies")
        df_markets = populate_markets()
        df_companies = populate_companies(df_bourso, df_eronext, df_markets)
        df_daystocks = populate_daystocks(df_eronext, df_companies)

    tps = time()
    df_stocks = populate_stocks(df_bourso, df_companies)
    tps_stocks = time() - tps


    tps = time()
    del df_bourso
    df_bourso = None
    del df
    df = None
    if not only_stocks:
        logger.info("pushing data to database")
        db.df_write(df_companies, "companies")
        db.df_write(df_daystocks, "daystocks")
    else:
        # df_existing = pd.read_csv("/tmp/stocks.csv.gz", compression="gzip")
        # df_stocks = pd.concat([df_existing, df_stocks])
        pass
    # df_stocks.to_csv("/tmp/stocks.csv.gz", index=False, compression="gzip")

    db.df_write(df_stocks, "stocks")
    tps = time()
    
    tps_create = time() - tps
    logger.info("tps_create: %s, tps_stocks %s", tps_create, tps_stocks)
    return df_markets, df_companies, 

def populate_companies(df_boursorama, df_euronext, df_market):
    """
    Merge Boursorama and Euronext dataframes to keep only:
      - name
      - isin       (from df_euronext)
      - symbol     (from df_boursorama)
      - boursorama (last price from df_boursorama)
      - euronext   (price from df_euronext)
      - mid        (market id from df_market, matched via the first 3 letters of boursorama code)
    """
    # only name, symbol & boursorama on the Bourso side
    small_bourso = df_boursorama[["name", "symbol", "boursorama"]]
    unique_bourso = (
        small_bourso
        .drop_duplicates(subset=["name", "symbol", "boursorama"])
        .sort_values(by=["name", "symbol"])
    )

    # name, isin & ticker on the Euronext side
    small_euronext = df_euronext[["name", "isin", "ticker"]]
    unique_euronext = (
        small_euronext
        .drop_duplicates(subset=["name", "isin", "ticker"])
        .sort_values(by=["name", "isin"])
    )
    
    # Merge on "name" — isin will come from Euronext
    merged_df = pd.merge(unique_bourso, unique_euronext, on="name", how="inner")
    merged_df.rename(columns={"ticker": "euronext"}, inplace=True)
    
    # Create market_prefix on companies side from first 3 chars of boursorama code
    merged_df["market_prefix"] = merged_df["boursorama"].str[:3]
    
    # Prepare market mapping from df_market using boursorama code prefix
    df_market2 = df_market.copy()
    df_market2["market_prefix"] = df_market2["boursorama"].str[:3]
    market_mapping = (
        df_market2[["market_prefix", "id"]]
        .rename(columns={"id": "mid"})
        .drop_duplicates("market_prefix")
    )
    
    # Merge to get mid based on market_prefix
    merged_df = merged_df.merge(market_mapping, on="market_prefix", how="left")
    merged_df.drop(columns="market_prefix", inplace=True)
    
    merged_df["pea"] = False
    merged_df["sector1"] = ""  # TODO
    merged_df["sector2"] = ""  # TODO
    merged_df["sector3"] = ""  # TODO

    # Ensure the values are integer
    merged_df["mid"] = merged_df["mid"].fillna(-1).astype(int)

    # Assign a new unique id for companies if needed
    merged_df["id"] = np.arange(len(merged_df))
    return merged_df



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