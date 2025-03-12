import pandas as pd
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import dash.dependencies as ddep
import plotly.express as px

from app import app, db

tab1_layout = html.Div([
    html.Div([
        html.H1("J'ai un changement"),
        
        # Sélecteur de période
        html.Div([
            html.Label("Choisissez la période:"),
            dcc.DatePickerRange(
                id='date-picker-range',
                start_date_placeholder_text="Début",
                end_date_placeholder_text="Fin",
                calendar_orientation='vertical'
            )
        ], className="date-picker-container"),
        
        # Sélecteur d'actions (multi-sélection)
        html.Div([
            html.Label("Choisissez vos actions :"),
            dcc.Dropdown(
                id="actions-dropdown",
                options=[
                    {'label': 'Action 1', 'value': 'action1'},
                    {'label': 'Action 2', 'value': 'action2'},
                    {'label': 'Action 3', 'value': 'action3'},
                    {'label': 'Action 4', 'value': 'action4'},
                ],
                multi=True,
                placeholder="Sélectionnez jusqu'à 2 actions"
            )
        ], className="actions-container"),
        
        html.Div(id="output-container")
    ], className="main-container"),
])