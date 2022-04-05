from numpy import size
from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
from preprocess import get_all_dataframes

app = Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

all_df = get_all_dataframes("out/")

fig = px.bar(all_df["info"], x="position", y="weight", barmode="group")

# method to find a player's id, given his name
def get_id_from_name(player_name):
    ids = all_df["info"]["id"]
    names = all_df["info"]["name"]
    for i in range (0, size(names)):
        if names[i] == player_name:
            return ids[i]
    raise ValueError("Player is not a valid player")

def plot_player_goals(player_name):
    player_id = get_id_from_name(player_name)
    ids = all_df["shooting"]["id"]
    seasons = all_df["shooting"]["season"]
    goals = all_df["shooting"]["goals"]
    for i in range (0, size(ids)):
        if ids[i] != player_id:
            seasons.pop(i)
            goals.pop(i)
    return px.line(x = seasons, y = goals, labels={'x':'seasons', 'y':'goals'})


# page layout

app.layout = html.Div(children=[
    html.H1(children='Information Visualization Project'),

    html.Div(children='''
        Soccer Stats
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    ),

    dcc.Graph(
        figure=plot_player_goals("Marco Benassi")
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)