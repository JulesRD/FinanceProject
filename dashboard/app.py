import numpy as np
import pandas as pd
import sqlalchemy
import datetime
import time

import dash
import dash_bootstrap_components as dbc

from mylogging import getLogger
import timescaledb_model as tsdb

mylogger = getLogger(__name__)

db = tsdb.TimescaleStockMarketModel('bourse', 'ricou', 'db', 'monmdp', remove_all=True)

## Boursorama

### MOCKING data
date_range = pd.date_range(start='2025-03-01', end='2025-04-01', freq='D')
value = np.random.uniform(low=10, high=100, size=100)
data = {
    'date': np.random.choice(date_range, size=100),
    'cid': np.random.randint(1, 5, size=100),  # Assuming 12 companies
    'value': np.random.uniform(low=10, high=100, size=100),
    'volume': np.random.uniform(low=100, high=1000, size=100),
}

daystocks_data = {
    'date': np.random.choice(date_range, size=100),
    'cid': np.random.randint(1, 5, size=100),
    'open': np.random.uniform(low=10, high=100, size=100),
    'close': np.random.uniform(low=10, high=100, size=100),
    'high': np.random.uniform(low=10, high=110, size=100),
    'low': np.random.uniform(low=0, high=90, size=100),
    'volume': np.random.uniform(low=100, high=1000, size=100),
    'mean': np.random.uniform(low=10, high=100, size=100),
    'std': np.random.uniform(low=1, high=10, size=100),
}

companies_data = {
    'id': np.arange(1, 5),
    'name': [f'Action {i}' for i in range(1, 5)],
    'mid': np.random.randint(1, 8, size=4),  # Assuming 7 markets
    'symbol': [f'SYM{i}' for i in range(1, 5)],
    'isin': [f'IS{i:010}' for i in range(1, 5)],
    'boursorama': [f'BOUR{i}' for i in range(1, 5)],
    'euronext': [f'EUR{i}' for i in range(1, 5)],
    'pea': np.random.choice([True, False], size=4),
    'sector1': [f'Sector1_{i}' for i in range(1, 5)],
    'sector2': [f'Sector2_{i}' for i in range(1, 5)],
    'sector3': [f'Sector3_{i}' for i in range(1, 5)],
}

df_stocks = pd.DataFrame(data)
df_daystocks = pd.DataFrame(daystocks_data)
df_companies = pd.DataFrame(companies_data)

db.df_write(df_companies, 'companies')
db.df_write(df_stocks, 'stocks')
db.df_write(df_daystocks, 'daystocks')

external_stylesheets=[dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__,  title="Bourse", suppress_callback_exceptions=True,
                external_stylesheets=external_stylesheets, assets_ignore='style.css?v=1.0')
app.df = df_stocks
app.daydf = df_daystocks
app.comp_names = []
server = app.server

from index import layout  # Not before app is defined since we use it
app.layout = layout

if __name__ == '__main__':
    app.run(debug=True)
