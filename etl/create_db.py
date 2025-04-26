import pandas as pd
import numpy as np

from timescaledb_model import initial_markets_data
import re

from mylogging import getLogger
from time import time
logger = getLogger(__name__)
import re

def clean_numeric_column_fast(series):
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
    Merge Boursorama et Euronext pour conserver :
      - name         (issu de Boursorama ou Euronext)
      - isin         (issu d'Euronext, NaN si manquant)
      - symbol       (clé de merge)
      - boursorama   (last price, issu de Boursorama, NaN si manquant)
      - euronext     (price issu d'Euronext, NaN si manquant)
      - mid          (market id de df_market basé sur les 3 premières lettres du code boursorama)
      - pea, sector1, sector2, sector3
    """

    # Côté Boursorama : garder name, symbol et boursorama
    small_bourso = df_boursorama[["name", "symbol", "boursorama"]]
    unique_bourso = (
        small_bourso.drop_duplicates(subset=["name", "symbol", "boursorama"])
        .sort_values(by=["name", "symbol"])
        .rename(columns={"name": "name_bourso"})
    )

    # Côté Euronext : garder name, isin et ticker (rajoute 'euronext') en créant une copie
    small_euronext = df_euronext[["name", "isin", "ticker"]].copy()
    small_euronext["euronext"] = small_euronext["ticker"]
    unique_euronext = (
        small_euronext.drop_duplicates(subset=["name", "isin", "ticker"])
        .sort_values(by=["isin"])
        .rename(columns={"name": "name_euronext", "ticker": "symbol"})
    )

    # Outer merge sur "symbol" pour conserver tous les enregistrements
    merged_df = pd.merge(unique_bourso, unique_euronext, on="symbol", how="outer", indicator=True, suffixes=("", ""))
    
    # Fusionner les noms : on privilégie le nom de Boursorama s'il existe, sinon celui d'Euronext
    merged_df["name"] = merged_df["name_bourso"].combine_first(merged_df["name_euronext"])
    merged_df.drop(columns=["name_bourso", "name_euronext", "_merge"], inplace=True)
    
    # Calculer le préfixe marché à partir du code boursorama et join avec df_market
    merged_df["market_prefix"] = merged_df["boursorama"].str[:3]
    df_market2 = df_market.copy()
    df_market2["market_prefix"] = df_market2["boursorama"].str[:3]
    market_mapping = (
        df_market2[["market_prefix", "id"]]
        .rename(columns={"id": "mid"})
        .drop_duplicates("market_prefix")
    )
    merged_df = merged_df.merge(market_mapping, on="market_prefix", how="left")
    merged_df.drop(columns="market_prefix", inplace=True)
    
    # Colonnes supplémentaires
    merged_df["pea"] = False
    merged_df["sector1"] = ""  # TODO
    merged_df["sector2"] = ""  # TODO
    merged_df["sector3"] = ""  # TODO
    
    # Convertir mid en int en remplaçant les valeurs manquantes par -1
    merged_df["mid"] = merged_df["mid"].fillna(-1).astype(int)
    
    # Optionnel : assigner un nouvel identifiant unique
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

def populate_stocks(df_boursorama: pd.DataFrame, df_companies: pd.DataFrame, save_path: str = "daystocks.parquet"):
    df_stocks = pd.DataFrame()

    # Reset index to avoid ambiguity with 'symbol', without adding the old index as a column
    df_boursorama = df_boursorama.reset_index(drop=True)
    df_companies = df_companies.reset_index(drop=True)

    # Merge df_boursorama with df_companies on the 'symbol' column
    merged_df = df_boursorama.merge(
        df_companies[['symbol', 'id', 'name']],
        how='left',
        left_on='name',
        right_on='name',
        suffixes=('', '_company')  # Avoid suffix conflicts
    )

    # Populate the stocks dataframe
    df_stocks["date"] = merged_df["date"]
    df_stocks["cid"] = merged_df["id"].fillna(-1).astype(int)  # Ensure 'cid' is an integer
    df_stocks["value"] = clean_numeric_column_fast(merged_df["last"])
    df_stocks["volume"] = merged_df["volume"]


    return df_stocks


def populate_daystocks(df_euronext: pd.DataFrame, df_companies: pd.DataFrame):
    # Merge des deux DataFrames
    merged_df = df_euronext.merge(
        df_companies[['isin', 'id']],
        how='left',
        on='isin'
    )

    # Initialisation du df final
    df_daystocks = pd.DataFrame()
    df_daystocks["date"] = merged_df["date"]
    df_daystocks["cid"] = merged_df["id"].fillna(-1).astype(int)

    # Colonnes à nettoyer
    numeric_cols = ["open", "close", "high", "low", "volume"]
    tps = time()
    df_daystocks[numeric_cols] = merged_df[numeric_cols].apply(clean_numeric_column_fast)
    print("Time to clean numeric columns:", time() - tps)

    # Calculs dérivés (mean et std après clean)
    df_daystocks["mean"] = (df_daystocks["high"] + df_daystocks["low"]) / 2
    df_daystocks["std"] = df_daystocks["high"] - df_daystocks["low"]
    # delete all nan
    df_daystocks = df_daystocks.dropna(subset=["volume", "open", "close"])

    return df_daystocks