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

    # Query the database for the selected actions and date range
    query = f"""
    SELECT date, action, value, open, low, high, close, 
    FROM stock_data
    WHERE action IN ({', '.join([f"'{action}'" for action in selected_actions])})
    AND date BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY date
    """

    mylogger.debug(f"\nQUERY: {query}\n")
    df = db.df_query(query)
    mylogger.debug(f"\ndf: {df}\n")
    #mylogger.debug(f"\n\n\nDF: {df}\n\n\n")
    # Create the graph
    if display_mode:
        fig = go.Figure(data=[go.Candlestick(x=df['date'],
                                            open=df['open'],
                                            high=df['high'],
                                            low=df['low'],
                                            close=df['close'])])
        fig.update_layout(title='Stock Values Over Time (Candlestick)')
    else:
        fig = px.line(df, x='date', y='value', color='action', title='Stock Values Over Time')
    # save de figure
    fig.write_image("./fig1.png")
    return fig


get_actions_query = f"""
SELECT DISTINCT action
FROM stock_data
ORDER BY action
"""
list_actions = db.df_query(get_actions_query)
list_actions = list(list_actions["action"])

print(list_actions)

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
                    {'label': action, 'value': action} for action in list_actions
                    ],
                multi=True,
                placeholder="Sélectionnez jusqu'à 2 actions"
            )
        ], className="actions-container"),

        # Sélecteur de mode d'affichage
        html.Div([
            html.Label("Mode d'affichage:"),
            dcc.Checkbox(
                id='display-mode-checkbox',
                value=False  # Default to line mode
            )
        ], className="display-mode-container"),

        # Graph for selected actions and date range
        html.Div([
            dcc.Graph(id='actions-graph')
        ], className="graph-container"),
        html.Div(id="output-container")
    ], className="main-container"),
])