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
    'action': np.random.choice(['Action 1', 'Action 2', 'Action 3', 'Action 4', 'Action 5', 'Action 6', 'Action 7', 'Action 8', 'Action 9', 'Action 10', 'Action 11', 'Action 12'], size=100),
    'value': np.random.uniform(low=10, high=100, size=100),

    # Ajouter des colonnes pour les valeurs open, high, low, close
    'open': np.random.uniform(low=10, high=100, size=100),
    'close': np.random.uniform(low=10, high=100, size=100),
}

data['high'] = data['value'] + np.random.uniform(low=0, high=10, size=100)
data['low'] = data['value'] - np.random.uniform(low=0, high=10, size=100)

print("\n\n\nEND_OF_DATA\n\n\n")
df = pd.DataFrame(data)
db.df_write(df, 'stock_data')
###

external_stylesheets=[dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__,  title="Bourse", suppress_callback_exceptions=True,
                external_stylesheets=external_stylesheets, assets_ignore='style.css?v=1.0')
app.df = df
app.daydf = pd.DataFrame()
app.comp_names = []
server = app.server

from index import layout  # Not before app is defined since we use it
app.layout = layout

if __name__ == '__main__':

    app.run(debug=True)
