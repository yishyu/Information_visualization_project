from numpy import size
from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
from preprocess import get_all_dataframes
from utils import time_this
import plotly.graph_objects as go

app = Dash("Information Visualization Project")

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

all_df = get_all_dataframes("out/")


@time_this
# method to find a player's id, given his name
def get_id_from_name(player_name):
    ids = all_df["info"]["id"]
    names = all_df["info"]["name"]
    for i in range (0, size(names)):
        if names[i] == player_name:
            return ids[i]
    raise ValueError(f"{player_name} is not a valid player")

@time_this
# method to find a player's id, given his name
def get_name_from_id(player_id):
    player_row = all_df["info"].loc[all_df["info"]["id"] == player_id]
    if len(player_row) == 0:
        raise ValueError(f"{player_id} is not a valid player")
    return player_row.iloc[0]["name"]


@time_this
def plot_player_goals(player_name):
    player_id = get_id_from_name(player_name)
    player_df = all_df["shooting"].loc[all_df["shooting"]["id"] == player_id]
    return px.line(x = player_df['season'], y = player_df['goals'], labels={'x':'seasons', 'y':'goals'})


def get_club_df(club_name, season, comp_level):
    return

def update_graph():
    print("hello")
    return


@time_this
def plot_a_club_players_cards(club_name, season, comp_level="1. Serie A"):
    clubs = all_df["info"]["club"].unique()
    seasons = all_df["misc"]["season"].unique()
    comp_levels = all_df["misc"]["comp_level"].unique()
    print(clubs)
    club_df = all_df["misc"].loc[
        (all_df["misc"]["squad"] == club_name) &
        (all_df["misc"]["season"] == season) &
        (all_df["misc"]["comp_level"] == comp_level)
    ]

    club_df = club_df.merge(all_df["info"], on="id", how="left")
    print(club_df["name"])
    button_layer_1_height = 1.08
    return go.Figure(
        data=[
            go.Bar(name="Red Cards", x=club_df["name"], y=club_df["cards_red"], marker=dict(color="red")),
            go.Bar(name='Yellow Cards', x=club_df["name"], y=club_df["cards_yellow"], marker=dict(color="yellow")),
        ],
        layout=go.Layout(
            title=go.layout.Title(text=f"Every cards gotten by {comp_level} {club_name} Players in {season}"),
            xaxis_title="Player Name",
            yaxis_title="Amount of Cards",
            font={
                "size": 15,
                "color": "black"
            },
            updatemenus=[
                dict(
                    buttons=list([
                        dict(
                            args=[update_graph(), club],
                            label=club,
                            method="restyle"
                        )
                        for club in clubs
                    ]),
                    direction="down",
                    pad={"l":450, "r": 10, "t": -60},
                    showactive=True,
                    x=0.1,
                    xanchor="left",
                    y=button_layer_1_height,
                    yanchor="top"
                ),
                dict(
                    buttons=list([
                        dict(
                            args=[update_graph(), comp_level],
                            label=comp_level,
                            method="restyle"
                        )
                        for comp_level in comp_levels
                    ]),
                    direction="down",
                    pad={"l":460, "r": 10, "t": -60},
                    showactive=True,
                    x=0.37,
                    xanchor="left",
                    y=button_layer_1_height,
                    yanchor="top"
                ),
                dict(
                    buttons=list([
                        dict(
                            args=[update_graph(), season],
                            label=season,
                            method="restyle"
                        )
                        for season in seasons
                    ]),
                    direction="down",
                    pad={"l":510, "r": 10, "t": -60},
                    showactive=True,
                    x=0.58,
                    xanchor="left",
                    y=button_layer_1_height,
                    yanchor="top"
                ),
            ]
        )
        )


@time_this
def plot_weight_by_position():
    return px.bar(all_df["info"], x="position", y="weight", barmode="group")

# page layout

app.layout = html.Div(children=[
    html.H1(children='Information Visualization Project'),

    html.Div(children='''
        Soccer Stats
    '''),

    # dcc.Graph(
    #     id='example-graph',
    #     figure=plot_weight_by_position
    # ),
    dcc.Graph(
        id='plot_a_club_players_cards',
        figure=plot_a_club_players_cards("Inter", "2015-2016")
    ),

    dcc.Graph(
        figure=plot_player_goals("Marco Benassi")
    )
])

if __name__ == '__main__':
    app.run_server(debug=False)