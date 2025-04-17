import pandas as pd
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import dash.dependencies as ddep
from dash.dependencies import Input, Output
from app import app, db
from mylogging import getLogger

mylogger = getLogger(__name__)

@app.callback(
    Output('raw-data-table', 'children'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('actions-dropdown', 'value')],
)
def update_table(start_date, end_date, selected_actions):
    if not start_date or not end_date or not selected_actions:
        return []

    # Query the daystocks table for the selected actions and date range
    query = f"""
    SELECT date, cid, MIN(low) as min, MAX(high) as max, open as begin, close as end, mean, std
    FROM daystocks
    WHERE cid IN ({', '.join([f"{cid}" for cid in selected_actions])})
    AND date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY date, cid, open, close, mean, std
    ORDER BY date
    """

    mylogger.debug(f"\nQUERY: {query}\n")
    df = db.df_query(query)
    mylogger.debug(f"\ndf: {df}\n")

    # Create the table rows
    rows = []
    for index, row in df.iterrows():
        rows.append(html.Tr([
            html.Td(row['date'].strftime('%Y-%m-%d')),
            html.Td(row['cid']),
            html.Td(f"{row['min']:.2f}"),
            html.Td(f"{row['max']:.2f}"),
            html.Td(f"{row['begin']:.2f}"),
            html.Td(f"{row['end']:.2f}"),
            html.Td(f"{row['mean']:.2f}"),
            html.Td(f"{row['std']:.2f}"),
        ]))

    # Create the table
    table = html.Table([
        html.Thead(html.Tr([
            html.Th('Date'),
            html.Th('Action ID'),
            html.Th('Min'),
            html.Th('Max'),
            html.Th('Début'),
            html.Th('Fin'),
            html.Th('Moyenne'),
            html.Th('Ecart-type'),
        ])),
        html.Tbody(rows)
    ], style={
        'margin': 'auto',
        'borderCollapse': 'collapse',
        'border': '1px solid #ddd',
        'backgroundColor': '#fff'
    })

    return table

get_actions_query = f"""
SELECT id, name
FROM companies
ORDER BY name
"""
list_actions = db.df_query(get_actions_query)
list_actions = list(list_actions.itertuples(index=False, name=None))

tab2_layout = html.Div([
    html.Div([
        html.H1("Données Brutes"),

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

        # Table for raw data
        html.Div([
            html.Div(id='raw-data-table', style={'overflowX': 'auto'})
        ], className="table-container", style={'margin': '20px auto'}),
    ], className="main-container"),
], style={'padding': '20px'})
