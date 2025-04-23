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

db = tsdb.TimescaleStockMarketModel('bourse', 'ricou', 'db', 'monmdp')

external_stylesheets=[dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__,  title="Bourse", suppress_callback_exceptions=True,
                external_stylesheets=external_stylesheets, assets_ignore='style.css?v=1.0')
server = app.server

from index import layout  # Not before app is defined since we use it
app.layout = layout

if __name__ == '__main__':
    app.run(debug=True)
