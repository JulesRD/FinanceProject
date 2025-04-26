import datetime

import pandas as pd
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
from dash.dependencies import Input, Output
from app import app, db
from mylogging import getLogger

mylogger = getLogger(__name__)

@app.callback(
    Output('actions-graph', 'figure'),
    Output('correlation-graph', 'figure'),
    Output('display-mode-checkbox', 'style'),
    Output('bollinger-mode-checkbox', 'style'),
    Output('correlation-container', 'style'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('actions-dropdown', 'value'),
     Input('display-mode-checkbox', 'value'),
     Input('bollinger-mode-checkbox', 'value')],
)
def update_graph(start_date, end_date, selected_actions, display_mode, bollinger_mode):
    if not start_date or not end_date or not selected_actions:
        return {}, {}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}

    # Determine if multiple actions are selected
    multiple_actions = len(selected_actions) > 1
    
    if multiple_actions:
        # Query the stocks table for line mode
        query = f"""
        SELECT date, cid, value
        FROM stocks
        WHERE cid IN ({', '.join([f"{cid}" for cid in selected_actions])})
        AND date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY date
        """
        display_mode = False  # Force line mode
        bollinger_mode = False  # Disable Bollinger Bands
    else:
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
        fig.update_layout(
            title='Stock Values Over Time (Candlestick)',
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=7, label="1W", step="day", stepmode="backward"),
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(visible=True),
                type="date"
            )
        )
    else:
        fig = px.line(df, x='date', y='value', color='cid', title='Stock Values Over Time')
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=7, label="1W", step="day", stepmode="backward"),
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(visible=True),
                type="date"
            )
        )

    if bollinger_mode and not multiple_actions:
        # Calculate Bollinger Bands
        window = 20  # Window size for the moving average
        df['SMA'] = df.groupby('cid')['value'].transform(lambda x: x.rolling(window=window).mean())
        df['RollingStd'] = df.groupby('cid')['value'].transform(lambda x: x.rolling(window=window).std())
        df['UpperBand'] = df['SMA'] + (df['RollingStd'] * 2)
        df['LowerBand'] = df['SMA'] - (df['RollingStd'] * 2)

        # Add Bollinger Bands to the graph
        for cid in selected_actions:
            df_cid = df[df['cid'] == cid]
            fig.add_trace(go.Scatter(x=df_cid['date'], y=df_cid['SMA'], mode='lines', name=f'SMA {cid}'))
            fig.add_trace(go.Scatter(x=df_cid['date'], y=df_cid['UpperBand'], mode='lines', name=f'Upper Band {cid}', line=dict(dash='dash')))
            fig.add_trace(go.Scatter(x=df_cid['date'], y=df_cid['LowerBand'], mode='lines', name=f'Lower Band {cid}', line=dict(dash='dash')))

    # --- Calcul et affichage de la matrice de corrélation ---
    corr_fig = {}
    if multiple_actions:
        # Aggregate duplicate entries by taking the mean of the values
        df = df.groupby(['date', 'cid']).mean().reset_index()

        # Pivot pour avoir une table avec chaque action en colonne
        pivot_df = df.pivot(index='date', columns='cid', values='value')
        corr_matrix = pivot_df.corr()

        corr_fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='Viridis',
            zmin=-1,
            zmax=1,
            colorbar=dict(title="Corrélation")
        ))

        corr_fig.update_layout(
            title="Corrélation entre les actions",
            xaxis_title="Action",
            yaxis_title="Action"
        )

    # Save the figure
    fig.write_image("./fig1.png")
    return fig, corr_fig, {'display': 'none' if multiple_actions else 'block'}, {'display': 'none' if multiple_actions else 'block'}, {'display': 'block' if multiple_actions else 'none'}

print("\n\nLoading companies...\n\n")
get_actions_query = f"""
SELECT id, name
FROM companies
ORDER BY name
"""
list_actions = db.df_query(get_actions_query)
print("\n\nlist_actions:\n", list_actions, "\n\n")
list_actions = list(list_actions.itertuples(index=False, name=None))

tab1_layout = html.Div([
    html.Div([
        html.H1("Graphique des cours"),

        # Sélecteur de période
        html.Div([
            html.Label("Choisissez la période:"),
            dcc.DatePickerRange(
                id='date-picker-range',
                start_date=datetime.date(2022, 1, 1),
                end_date=datetime.date(2022, 12, 31),
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
                options=[{'label': 'Chandeliers', 'value': True}],
                value=[],  # Default to line mode
                switch=True,
            ),
            dbc.Checklist(  # Use Checklist from dash_bootstrap_components
                id='bollinger-mode-checkbox',
                options=[{'label': 'Bandes de Bollinger', 'value': True}],
                value=[],  # Default to line mode
                switch=True,
            )
        ], className="display-mode-container"),

        # Graph for selected actions and date range
        html.Div([
            dcc.Graph(id='actions-graph'),
            # Matrice de corrélation
            html.Div([
                html.H4("Matrice de corrélation"),
                dcc.Graph(id='correlation-graph')
            ], id='correlation-container'),
        ], className="graph-container"),
        html.Div(id="output-container")
    ], className="main-container"),
])
