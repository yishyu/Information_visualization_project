import numpy as np
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
from preprocess import get_all_dataframes
from utils import time_this
import plotly.graph_objects as go
from plotly.subplots import make_subplots

app = Dash("Information Visualization Project")

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

all_df = get_all_dataframes("out/")


@time_this
# method to find a player's id, given his name
def get_id_from_name(player_name):
    ids = all_df["info"]["id"]
    names = all_df["info"]["name"]
    for i in range (0, np.size(names)):
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
    #fig = px.line(x = player_df['season'], y = player_df['goals_per_shot_on_target'], color=px.Constant("Scoring percentage on attempts on goal"), 
    #              labels={'x':'seasons', 'y':'goals'})
    #fig.add_bar(x = player_df['season'], y = player_df['goals'], name = "Actual goals")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(name = "Actual goals", x = player_df['season'], y = player_df['goals']),
        secondary_y = False,
    )
    fig.add_trace(
        go.Scatter(x = player_df['season'], y = player_df['goals_per_shot_on_target'], name = "Scoring percentage on attempts on goal"), 
        secondary_y = True,
    )
    fig.update_xaxes(title_text = "season")
    fig.update_yaxes(title_text = "goals", secondary_y = False)
    fig.update_yaxes(title_text = "percentage", secondary_y = True)
    return fig

@time_this
@app.callback(
    Output('plot_a_club_players_cards', 'figure'),
    Input('club_dropdown', 'value'),
    Input('season_dropdown', 'value'),
    Input('comp_level_dropdown', 'value')
)
def plot_a_club_players_cards(club_name, season, comp_level):

    clubs = all_df["info"]["club"].unique()
    seasons = all_df["misc"]["season"].unique()
    comp_levels = all_df["misc"]["comp_level"].unique()
    club_df = all_df["misc"].loc[
        (all_df["misc"]["squad"] == club_name) &
        (all_df["misc"]["season"] == season) &
        (all_df["misc"]["comp_level"] == comp_level)
    ]

    club_df = club_df.merge(all_df["info"], on="id", how="left")
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
        )
    )


@app.callback(
    Output('season_dropdown', 'value'),
    Output('season_dropdown', 'options'),
    Output('comp_level_dropdown', 'value'),
    Output('comp_level_dropdown', 'options'),
    Input('club_dropdown', 'value'),
)
def update_dropdowns(club_name):
    seasons = all_df["misc"].sort_values("season", ascending=False)["season"].loc[all_df["misc"]["squad"] == club_name].unique()
    season = seasons[0]
    comp_levels = all_df["misc"].sort_values("comp_level")["comp_level"].loc[all_df["misc"]["squad"] == club_name].unique()
    comp_level = comp_levels[0]
    return season, seasons, comp_level, comp_levels


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
    html.Div(
        className="row",
        children=[
            html.Div(
                className="four columns", children=[
                dcc.Dropdown(
                    all_df["misc"].sort_values("squad")["squad"].unique(),
                    all_df["misc"].sort_values("squad")["squad"].unique()[0],
                    id='club_dropdown',
                    placeholder="Select a Club"
                ),
            ]),
            html.Div(
                className="four columns", children=[
                dcc.Dropdown(
                    id='season_dropdown',
                    placeholder="Select a season",
                ),
            ]),
            html.Div(
                className="four columns", children=[
                dcc.Dropdown(
                    id='comp_level_dropdown',
                    placeholder="Select a competitive level"
                ),
            ]),
        ]
    ),

    dcc.Graph(id='plot_a_club_players_cards'),
    dcc.Graph(
        figure=plot_player_goals("Romelu Lukaku")
    )
])

if __name__ == '__main__':
    app.run_server(debug=False)