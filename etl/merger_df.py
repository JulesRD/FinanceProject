import pandas as pd
import numpy as np


def merge_dataset(df_boursorama, df_euronext, delete_name_alone=True):
    # delete_name_alone : delete the rows when the name is only in bourso and not in euronext
    if delete_name_alone:
        # Filter rows where the name exists in both datasets
        df_boursorama2 = df_boursorama[df_boursorama['name'].isin(df_euronext['name'])].copy()
    else:
        df_boursorama2 = df_boursorama.copy()

    # Get all unique columns from both datasets
    all_columns = list(set(df_euronext.columns).union(set(df_boursorama2.columns)))

    # Ensure both dataframes have the same columns
    for col in all_columns:
        if col not in df_euronext.columns:
            df_euronext[col] = np.nan
        if col not in df_boursorama2.columns:
            df_boursorama2[col] = np.nan

    # Concatenate the two datasets
    df = pd.concat([df_boursorama2, df_euronext], ignore_index=True)

    # Fill missing 'isin' values in df with the mapping from df_euronext
    isin_mapping = df_euronext.set_index('name')['isin'].to_dict()
    df['isin'] = df['isin'].fillna(df['name'].map(isin_mapping))

    # Remove duplicates based on all columns
    

    # Optionally, you can remove duplicates based on specific columns (e.g., 'name' and 'isin')
    # df = df.drop_duplicates(subset=['name', 'isin'])

    # TODO: Fill the other variables with the euronext values
    # TODO: Fill the 'symbol' value in the euronext with the bourso value

    return df