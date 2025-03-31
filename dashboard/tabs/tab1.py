import pandas as pd
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import dash.dependencies as ddep
import plotly.express as px
from dash.dependencies import Input, Output
from app import app, db
from mylogging import getLogger

mylogger = getLogger(__name__)

@app.callback(
    Output('actions-graph', 'figure'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('actions-dropdown', 'value'),
     Input('display-mode-checkbox', 'value')],
)
def update_graph(start_date, end_date, selected_actions, display_mode):
    if not start_date or not end_date or not selected_actions:
        return {}

    if display_mode:
        # Query the daystocks table for candlestick mode
        query = f"""
        SELECT date, cid, open, low, high, close
        FROM daystocks
        WHERE cid IN ({', '.join([f"{cid}" for cid in selected_actions])})
        AND date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY date
        """
    else:
        # Query the stocks table for line mode
        query = f"""
        SELECT date, cid, value
        FROM stocks
        WHERE cid IN ({', '.join([f"{cid}" for cid in selected_actions])})
        AND date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY date
        """

    mylogger.debug(f"\nQUERY: {query}\n")
    df = db.df_query(query)
    mylogger.debug(f"\ndf: {df}\n")

    # Create the graph
    if display_mode:
        fig = go.Figure(data=[go.Candlestick(x=df['date'],
                                             open=df['open'],
                                             high=df['high'],
                                             low=df['low'],
                                             close=df['close'])])
        fig.update_layout(title='Stock Values Over Time (Candlestick)')
    else:
        fig = px.line(df, x='date', y='value', color='cid', title='Stock Values Over Time')

    # Save the figure
    fig.write_image("./fig1.png")
    return fig

get_actions_query = f"""
SELECT id, name
FROM companies
ORDER BY name
"""
list_actions = db.df_query(get_actions_query)
list_actions = list(list_actions.itertuples(index=False, name=None))

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
            html.Label("Choisissez vos actions parmis les suivantes:"),
            dcc.Dropdown(
                id="actions-dropdown",
                options=[
                    {'label': name, 'value': cid} for cid, name in list_actions
                ],
                multi=True,
                placeholder="Sélectionnez jusqu'à 2 actions"
            )
        ], className="actions-container"),

        # Sélecteur de mode d'affichage
        html.Div([
            html.Label("Mode d'affichage:"),
            dbc.Checklist(  # Use Checklist from dash_bootstrap_components
                id='display-mode-checkbox',
                options=[{'label': 'Candlestick', 'value': True}],
                value=[],  # Default to line mode
                switch=True,
            )
        ], className="display-mode-container"),

        # Graph for selected actions and date range
        html.Div([
            dcc.Graph(id='actions-graph')
        ], className="graph-container"),
        html.Div(id="output-container")
    ], className="main-container"),
])
