import pandas as pd
import glob
import os
import re
import numpy as np
import datetime
from mylogging import getLogger
HOME = "/home/bourse/data/"
logger = getLogger(__name__)

def load_dataset(data_path, n):
    # Print the number of files in the directory
    files = os.listdir(data_path)
    print(f"Number of files in the directory: {len(files)}")

    # Use glob to get all files that start with 'Euronext_Equities_' and end with .csv or .xlsx
    file_pattern = os.path.join(data_path, "Euronext_Equities_*.*")
    files = glob.glob(file_pattern)

    # List to store individual dataframes
    df_list = []
    counter = 0

    # Loop through each file and process based on file extension
    for file in files:
        if counter % 100 == 0:
            logger.info(f"Processing file {counter}")
        if counter == n:
            break
        try:
            if file.lower().endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8', sep='\t')
            elif file.lower().endswith('.xlsx'):
                df = pd.read_excel(file)
            else:
                # Skip unknown file types
                print("Unsupported file type")
                continue

            # Extract the date from the filename using a regex (assuming format YYYY-MM-DD)
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(file))
            if date_match:
                file_date = date_match.group(1)
                # Add the second and milisecond to the date
                file_date = file_date + " 00:00:00.000000"
                file_date = datetime.datetime.strptime(file_date, '%Y-%m-%d %H:%M:%S.%f')
                # Add the date as a new column (as datetime type)
                df['date'] = file_date
            else:
                # Optionally log or handle files without a proper date in the filename
                df['file_date'] = pd.NaT

            # Append the dataframe to the list
            df_list.append(df)
            counter += 1
        except Exception as e:
            print(f"Error processing file {file}: {e}")

    return df_list

def get_df(n):
    # Define the path to the directory containing the files
    data_path = HOME + "euronext"

    df_list = load_dataset(data_path, n)

    # Concatenate all dataframes into one robust dataframe
    if df_list:
        combined_df = pd.concat(df_list, ignore_index=True)
    else:
        combined_df = pd.DataFrame()

    # Standardize column names: trim whitespace, lower case, and replace spaces with underscores
    combined_df.columns = combined_df.columns.str.strip().str.lower().str.replace(' ', '_')

    # Define a mapping of equivalent column names to merge differences between CSV and XLSX files
    column_synonyms = {
        'ticker': ['ticker', 'symbol'],
        'name': ['company', 'company_name', 'name'],
        'price': ['price', 'closing_price', 'last_price', 'last'],
        'currency': ['currency', 'trading_currency'],
        'open': ['open', 'open_price'],
        'high': ['high', 'high_price'],
        'low': ['low', 'low_price'],
        'last_trade_time': ['last_trade_time', 'last_trade_mic_time', 'last_date/time']
    }

    # Merge equivalent columns
    for canonical, synonyms in column_synonyms.items():
        # Find which of the synonym columns are present in the dataframe
        cols_present = [col for col in synonyms if col in combined_df.columns]
        if len(cols_present) > 1:
            # Merge the columns: use the first non-null value among the columns
            combined_df[canonical] = combined_df[cols_present[0]].combine_first(combined_df[cols_present[1]])
            for col in cols_present[2:]:
                combined_df[canonical] = combined_df[canonical].combine_first(combined_df[col])
            # Drop the extra synonym columns, keeping the canonical one
            for col in cols_present:
                if col != canonical:
                    combined_df.drop(columns=col, inplace=True)
        elif len(cols_present) == 1 and cols_present[0] != canonical:
            # Rename the column to the canonical name
            combined_df.rename(columns={cols_present[0]: canonical}, inplace=True)

    # Remove the closing price column if it exists
    if 'closing_price_datetime' in combined_df.columns:
        combined_df.drop(columns='closing_price_datetime', inplace=True)

    # Optionally, drop duplicates
    combined_df.drop_duplicates(inplace=True)

    # Remove the rows where the isin value is NaN
    combined_df = combined_df[~combined_df['isin'].isna()]

    # Add a new column 'pea' based on the currency column
    if 'currency' in combined_df.columns:
        combined_df['pea'] = combined_df['currency'].apply(
            lambda x: True if isinstance(x, str) and x.upper() == 'EUR' else False)
    else:
        combined_df['pea'] = False

    # Reset the index of the dataframe
    combined_df.reset_index(drop=True, inplace=True)

    #   Replace invalid values with NaN
    combined_df["high"] = combined_df["high"].replace('-', np.nan)
    combined_df["low"] = combined_df["low"].replace('-', np.nan)

    # Convert columns to float
    combined_df["high"] = combined_df["high"].astype(float)
    combined_df["low"] = combined_df["low"].astype(float)
    
    # Trier les données par 'isin' et 'date' pour garantir l'ordre correct
    if 'isin' in combined_df.columns and 'date' in combined_df.columns:
        combined_df.sort_values(by=['isin', 'date'], inplace=True)

    # Ajouter une colonne 'close' qui correspond à la valeur 'open' du jour suivant pour chaque 'isin'
    if 'open' in combined_df.columns:
        combined_df['close'] = combined_df.groupby('isin')['open'].shift(-1)
    else:
        combined_df['close'] = pd.NA

    # Réinitialiser l'index après avoir ajouté la colonne 'close'
    combined_df.reset_index(drop=True, inplace=True)

    return combined_df
