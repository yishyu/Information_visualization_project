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
                "size": 12,
                "color": "black"
            },
        )
    )

@time_this
@app.callback(
    Output('plot_a_player_fouls_cards_seasons', 'figure'),
    Input('player_dropdown', 'value'),
)
def plot_a_player_fouls_cards_seasons(player_name):
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
                "size": 12,
                "color": "black"
            },
        )
    )

@time_this
@app.callback(
    # Output('position_dropdown', 'value'),
    # Output('position_dropdown', 'options'),
    Output('player_dropdown', 'value'),
    Output('player_dropdown', 'options'),
    Input('position_dropdown', 'value'),
)
def update_dropdowns(position):
    players = all_df["info"].sort_values("name")["name"].loc[all_df["info"]["position"] == position].unique()
    player = players[0]
    return player, players


@time_this
@app.callback(
    Output('height', 'children'),
    Output('weight', 'children'),
    Input('player_dropdown', 'value'),
)
def get_player_weight_height(player_name):
    player_row = all_df["info"].loc[all_df['info']['name'] == player_name]
    height = player_row.iloc[0]["height"]
    weight = player_row.iloc[0]["weight"]
    return f"Height: {height} cm", f"Weight: {weight} kg"

@time_this
@app.callback(
    Output('plot_a_player_clubs_seasons', 'figure'),
    Input('player_dropdown', 'value'),
)
def get_player_club_evolution(player_name):
    player_id = get_id_from_name(player_name)
    player_misc_df = all_df["misc"].loc[all_df["misc"]["id"] == player_id]
    figure = go.Figure()
    values = player_misc_df["squad"].value_counts()
    figure.add_trace(
        go.Pie(labels=values.index.tolist(), values=values.tolist(), textinfo='label+percent')
    )
    figure.update_layout(
        title=go.layout.Title(text=f"{player_name} all clubs from his career and played time percentage"),
        font={
                "size": 12,
                "color": "black"
            },
    )
    return figure

@time_this
@app.callback(
    Output('plot_a_player_tackles', 'figure'),
    Input('player_dropdown', 'value'),
)
def get_player_tackles(player_name):
    player_id = get_id_from_name(player_name)
    player_def_df = all_df["defense"].loc[all_df["defense"]["id"] == player_id]

    fig = go.Figure(data=[
        go.Bar(name="won tackles", x=player_def_df["season"], y=player_def_df["tackles_won"], marker=dict(color="Green")),
        go.Bar(name="all tackles", x=player_def_df["season"], y=player_def_df["tackles"])
    ])
    return fig

# page layout

app.layout = html.Div(children=[
    html.H1(children='Information Visualization Project'),
    html.H2(children='Soccer Statistics'),
    # dcc.Graph(
    #     id='example-graph',
    #     figure=plot_weight_by_position
    # ),
    html.Div(
        className="row",
        children=[
            html.Div( ## Date select dcc components
                [
                    dcc.Markdown("Choose a field position"),
                    dcc.Dropdown(
                        all_df["info"].sort_values("position")["position"].unique(),
                        all_df["info"].sort_values("position")["position"].unique()[0],
                        id='position_dropdown',
                        placeholder="Select a field position"
                    ),
                ],
                style={
                    "display": "inline-block",
                    "width": "40%",
                    "margin-left": "20px",
                    "verticalAlign": "top"
                }
            ),
            html.Div( ## Stock select
            [
                dcc.Markdown("Choose a Player"),
                dcc.Dropdown(
                    all_df["info"].sort_values("name")["name"].unique(),
                    all_df["info"].sort_values("name")["name"].unique()[0],
                    id='player_dropdown',
                    placeholder="Select a player"
                ),
            ],
            style={
                "display": "inline-block",
                "width": "15%"
            }
        ),
        ]
    ),

    html.Div(children=[
        html.Span(id="height"),
    ]),
    html.Div(children=[
        html.Span(id="weight"),
    ]),
    html.Div(children=[
        dcc.Graph(
            id="plot_a_player_clubs_seasons",
        ),
        dcc.Graph(
            id="plot_a_player_cards_seasons",
            style={
                "display": "inline-block",
                "width": "40%",
            }
        ),
        dcc.Graph(
            id="plot_a_player_fouls_cards_seasons",
            style={
                "display": "inline-block",
                "width": "40%",
                "verticalAlign": "top"
            }
        ),

    ]),
    dcc.Graph(
            id="plot_a_player_tackles",
    ),
    dcc.Graph(
            id="plot_a_player_assists",
    ),
    dcc.Graph(
        figure=plot_player_goals("Romelu Lukaku")
    )
])

if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)