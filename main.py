from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
from preprocess import get_all_dataframes

app = Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

all_df = get_all_dataframes("out/")

fig = px.bar(all_df["info"], x="position", y="weight", barmode="group")

app.layout = html.Div(children=[
    html.H1(children='Information Visualization Project'),

    html.Div(children='''
        Soccer Stats
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)