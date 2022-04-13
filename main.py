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
    Output('plot_a_player_cards_seasons', 'figure'),
    Input('player_dropdown', 'value'),
)
def plot_a_player_cards_seasons(player_name):
    player_id = get_id_from_name(player_name)
    player_misc_df = all_df["misc"].loc[all_df["misc"]["id"] == player_id]

    button_layer_1_height = 1.08
    return go.Figure(
        data=[
            go.Bar(name="Red Cards", x=player_misc_df["season"].unique(), y=player_misc_df["cards_red"], marker=dict(color="red"), offsetgroup=0),
            go.Bar(name='Yellow Cards', x=player_misc_df["season"].unique(), y=player_misc_df["cards_yellow"], marker=dict(color="#FFEA00"), offsetgroup=1),
        ],
        layout=go.Layout(
            barmode="group",
            title=go.layout.Title(text=f"Every cards gotten by {player_name} throughout the seasons"),
            xaxis_title="Seasons",
            yaxis_title="Amount of Cards",
            font={
                "size": 15,
                "color": "black"
            },
        )
    )

@time_this
@app.callback(
    Output('plot_a_player_height_weight_seasons', 'figure'),
    Input('player_dropdown', 'value'),
)
def plot_a_player_height_weight_seasons(player_name):
    player_id = get_id_from_name(player_name)
    player_misc_df = all_df["misc"].loc[all_df["misc"]["id"] == player_id]
    player_misc_df["cards"] = player_misc_df["cards_red"] + player_misc_df["cards_yellow"]
    button_layer_1_height = 1.08
    return go.Figure(
        data=[
            go.Scatter(name='Cards Got', x=player_misc_df["season"].unique(), y=player_misc_df["cards"], marker=dict(color="Orange")),
            go.Scatter(name='Number of Fouls', x=player_misc_df["season"].unique(), y=player_misc_df["fouls"], marker=dict(color="#008000")),
        ],
        layout=go.Layout(
            barmode="group",
            title=go.layout.Title(text=f"Comparison between the amount of faults and the number of cards gotten by {player_name} throughout the seasons"),
            xaxis_title="Seasons",
            yaxis_title="Unity",
            font={
                "size": 15,
                "color": "black"
            },
        )
    )


# @app.callback(
#     Output('position_dropdown', 'value'),
#     Output('position_dropdown', 'options'),
#     Output('player_dropdown', 'value'),
#     Output('player_dropdown', 'options'),
#     Input('comp_level_dropdown', 'value'),
# )
# def update_dropdowns(comp_level):
#
#     positions = all_df["info"].sort_values("position", ascending=False)["position"].loc[all_df["misc"]["comp_level"] == comp_level].unique()
#     position = positions[0]
#     players = all_df["misc"].sort_values("player")["player"].loc[all_df["misc"]["comp_level"] == comp_level].unique()
#     player = players[0]
#     return position, positions, player, players


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
            # html.Div(
            #     className="four columns", children=[
            #     dcc.Dropdown(
            #         all_df["misc"].sort_values("comp_level")["comp_level"].unique(),
            #         all_df["misc"].sort_values("comp_level")["comp_level"].unique()[0],
            #         id='comp_level_dropdown',
            #         placeholder="Select a Level"
            #     ),
            # ]),
            # html.Div(
            #     className="four columns", children=[
            #     dcc.Dropdown(
            #         id='position_dropdown',
            #         placeholder="Select a position",
            #     ),
            # ]),
            html.Div(
                className="four columns", children=[
                dcc.Dropdown(
                    all_df["info"].sort_values("name")["name"].unique(),
                    all_df["info"].sort_values("name")["name"].unique()[0],
                    id='player_dropdown',
                    placeholder="Select a player"
                ),
            ]),
        ]
    ),

    dcc.Graph(
        id="plot_a_player_cards_seasons",
        ),
    dcc.Graph(
        id="plot_a_player_height_weight_seasons",
        ),
    dcc.Graph(
        figure=plot_player_goals("Romelu Lukaku")
    )
])

if __name__ == '__main__':
    app.run_server(debug=False)