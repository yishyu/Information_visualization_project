import numpy as np
from dash import Dash, html, dcc, Input, Output, callback_context
import plotly.express as px
import pandas as pd
from preprocess import get_all_dataframes
from utils import time_this
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
import os
import base64


app = Dash(__name__)

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
# @app.callback(
#     Output('plot_player_goals', 'figure'),
#     Input('player_dropdown', 'value'),
# )
def plot_player_goals(player_name):
    player_id = get_id_from_name(player_name)
    try:
        player_df = all_df["shooting"].loc[all_df["shooting"]["id"] == player_id]

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        teams = player_df['squad']

        # for the goals (bar plot)
        idx_change_of_teams = 0
        for i in range (1, len(teams)):
            if((teams.get(i) != teams.get(i-1)) or (i == len(teams)-1)):
                fig.add_trace(
                    go.Bar(
                        name = f"Actual goals for {teams.get(idx_change_of_teams)}",
                        x = [player_df['season'][j] for j in range(idx_change_of_teams,i)],
                        y = [player_df['goals'][j] for j in range(idx_change_of_teams,i)]),
                        secondary_y = False,
                )
                idx_change_of_teams = i

        # for the scoring percentage (scatter plot)
        idx_change_of_teams = 0
        for i in range (1, len(teams)):
            if((teams.get(i) != teams.get(i-1)) or (i == len(teams)-1)):
                fig.add_trace(
                    go.Scatter(
                        x = [player_df['season'][j] for j in range(idx_change_of_teams,i)],
                        y = [player_df['goals_per_shot_on_target'][j] for j in range(idx_change_of_teams,i)],
                        name = f"Scoring percentage on attempts on goal for {teams.get(idx_change_of_teams)}"),
                        secondary_y = True,
                )
                idx_change_of_teams = i

        fig.update_xaxes(title_text = "season")
        fig.update_yaxes(title_text = "goals", secondary_y = False)
        fig.update_yaxes(title_text = "percentage", secondary_y = True)

    except:
        fig = go.Figure()
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
    Output('plot_player_games_played', 'figure'),
    Input('player_dropdown', 'value'),
)
def plot_player_games_played(player_name):
    player_id = get_id_from_name(player_name)
    player_df = all_df["playing_time"].loc[all_df["playing_time"]["id"] == player_id]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    teams = player_df['squad']

    # for the games played (bar plot)
    idx_change_of_teams = 0
    for i in range (1, len(teams)):
        if((teams.get(i) != teams.get(i-1)) or (i == len(teams)-1)):
            fig.add_trace(
                go.Bar(
                    name = f"Games played for {teams.get(idx_change_of_teams)}",
                    x = [player_df['season'][j] for j in range(idx_change_of_teams,i)],
                    y = [player_df['games'][j] for j in range(idx_change_of_teams,i)]),
                    secondary_y = False,
            )
            idx_change_of_teams = i

    # for the scoring percentage (scatter plot)
    idx_change_of_teams = 0
    for i in range (1, len(teams)):
        if((teams.get(i) != teams.get(i-1)) or (i == len(teams)-1)):
            fig.add_trace(
                go.Scatter(
                    x = [player_df['season'][j] for j in range(idx_change_of_teams,i)],
                    y = [player_df['minutes_per_game'][j] for j in range(idx_change_of_teams,i)],
                    name = f"Minutes per game for {teams.get(idx_change_of_teams)}"),
                    secondary_y = True,
            )
            idx_change_of_teams = i

    fig.update_xaxes(title_text = "season")
    fig.update_yaxes(title_text = "games", secondary_y = False)
    fig.update_yaxes(title_text = "minutes", secondary_y = True)
    fig.update_layout(
        title=go.layout.Title(text=f"{player_name} games played vs minutes per game"),
        font={
                "size": 12,
                "color": "black"
            },
    )
    return fig

@time_this
@app.callback(
    Output('plot_a_player_tackles', 'figure'),
    Input('player_dropdown', 'value'),
)
def get_player_tackles(player_name):
    player_id = get_id_from_name(player_name)
    player_def_df = all_df["defense"].loc[all_df["defense"]["id"] == player_id]

    # fig = go.Figure(data=[
    #     go.Bar(name="won tackles", x=player_def_df["season"], y=player_def_df["tackles_won"], marker=dict(color="Green")),
    #     go.Bar(name="all tackles", x=player_def_df["season"], y=player_def_df["tackles"])
    # ])

    fig = go.Figure()
    teams = player_def_df['squad']

    idx_change_of_teams = 0
    for i in range (1, len(teams)):
        if((teams.get(i) != teams.get(i-1)) or (i == len(teams)-1)):
            fig.add_trace(
                    go.Bar(
                        name=f"won tackles for {teams.get(idx_change_of_teams)}",
                        x=[player_def_df["season"][j] for j in range(idx_change_of_teams,i)],
                        y=[player_def_df["tackles_won"][j] for j in range(idx_change_of_teams,i)],
                        marker=dict(color="Green"))
                    )
            fig.add_trace(
                    go.Bar(
                        name=f"all tackles for {teams.get(idx_change_of_teams)}",
                        x=[player_def_df["season"][j] for j in range(idx_change_of_teams,i)],
                        y=[player_def_df["tackles"][j] for j in range(idx_change_of_teams,i)])
                    )
            idx_change_of_teams = i
    return fig

@time_this
@app.callback(
    Output('plot_a_player_assists', 'figure'),
    Input('player_dropdown', 'value')
)
def get_player_assists(player_name):
    player_id = get_id_from_name(player_name)
    player_pass_df = all_df["passing"].loc[all_df["passing"]["id"] == player_id][["season", "passes_short", "passes_medium", "passes_long", "assists"]]
    # player_pass_df = player_pass_df.fillna(-100)
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    for name, values in player_pass_df.iteritems():
        if name == "assists":
            figure.add_trace(
                go.Scatter(name=name, x=player_pass_df["season"], y=values), secondary_y=True
            )
        elif name != "season":
            figure.add_trace(
                go.Bar(name=name, x=player_pass_df["season"], y=values), secondary_y=False
            )

    figure.update_xaxes(title_text = "season")
    figure.update_yaxes(title_text = "passes", secondary_y = False)
    figure.update_yaxes(title_text = "assists", secondary_y = True)
    figure.update_layout(
        barmode="stack",
        title=go.layout.Title(text=f"{player_name} passes stats"),
        font={
                "size": 12,
                "color": "black"
            },
    )
    return figure



@app.callback(
    Output('container-button-timestamp', 'children'),
    Input('keeper', 'n_clicks'),
    Input('defender', 'n_clicks'),
    Input('midfielder', 'n_clicks'),
    Input('striker', 'n_clicks')
)
def displayClick(btn1, btn2, btn3, btn4):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'keeper' in changed_id:
        msg = 'Button 1 was most recently clicked'
    elif 'defender' in changed_id:
        msg = 'Button 2 was most recently clicked'
    elif 'midfielder' in changed_id:
        msg = 'Button 3 was most recently clicked'
    elif 'striker' in changed_id:
        msg = "mqlsekjflds"
    else:
        msg = 'None of the buttons have been clicked yet'
    return html.Div(msg)

@time_this
@app.callback(
    Output('gk_graph', 'figure'),
    Input('player_dropdown', 'value')
)
def plot_gk(player_name, category="clean sheets"):
    player_id = get_id_from_name(player_name)
    player_df = all_df["keeper"].loc[all_df["keeper"]["id"] == player_id]

    if category == "clean sheets":
        column = "clean_sheets"
        column2 = "clean_sheets_pct"
        yaxes = "Clean sheets"
        yaxes2 = "Clean sheets percentage"
    elif category == "saves":
        column = "shots_on_target_against"
        column2 = "save_pct"
        yaxes = "Shots on target"
        yaxes2 = "Save percentage"
    elif category == "penalties":
        column = "pens_att_gk"
        column2 = "pens_save_pct"
        yaxes = "Penalties against"
        yaxes2 = "Penalty save percentage"

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(name = yaxes, x = player_df["season"], y = player_df[column]),
        secondary_y = False,
    )

    fig.add_trace(
        go.Scatter(name = yaxes2, x = player_df["season"], y = player_df[column2]),
        secondary_y = True
    )
    fig.update_xaxes(title_text = "season")
    fig.update_yaxes(title_text = yaxes)
    fig.update_yaxes(title_text = yaxes2, secondary_y = True)
    return fig

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == "/" :
        image_filename = "assets/soccerfield.png"
        soccerfield = base64.b64encode(open(image_filename, 'rb').read())
        return html.Div(children=[
            html.H2(children='Soccer Statistics : Select the position you are looking for'),
            html.Div(
                children=[
                    html.Img(src=f'data:image/png;base64,{soccerfield.decode()}', style={"width": "60%", "margin": "auto", "display": "block"}),
                    html.Div(
                        id="overlay",
                        children=[
                            dcc.Link(html.Button('Keepers', className="positionBtn", id='keeper', n_clicks=0), href='/keeper'),
                            dcc.Link(html.Button('Defenders', className="positionBtn rectangleBtn", id='defender', n_clicks=0), href='/defender'),
                            dcc.Link(html.Button('Midfielders', className="positionBtn rectangleBtn", id='midfielder', n_clicks=0), href='/midfielder'),
                            dcc.Link(html.Button('Strikers', className="positionBtn rectangleBtn", id='striker', n_clicks=0), href='/striker'),

                        ]
                    ),
                ]
                ),
        ])
    else:

        position_shortcuts = {"/midfielder": "M", "/keeper": "G", "/defender": "D", "/striker": "A"}
        position_shortcut = position_shortcuts[pathname]
        return html.Div(children=[
            html.Div(
                className="row",
                children=[
                    html.Div( ## Date select dcc components
                        [
                            dcc.Markdown("Choose a field position"),
                            dcc.Dropdown(
                                all_df["info"].loc[all_df["info"]["position"].str.contains(position_shortcut)].sort_values("position")["position"].unique(),
                                all_df["info"].loc[all_df["info"]["position"].str.contains(position_shortcut)].sort_values("position")["position"].unique()[0],
                                id='position_dropdown',
                                placeholder="Select a field position"
                            ),
                        ],
                        style={
                            "display": "inline-block",
                            "width": "40%",
                            "marginLeft": "20px",
                            "verticalAlign": "top"
                        }
                    ),
                    html.Div( ## Stock select
                    [
                        dcc.Markdown("Choose a Player"),
                        dcc.Dropdown(
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
                id="plot_player_games_played",
                # figure=plot_player_games_played("Marco Benassi")
            ),
            dcc.Graph(
                    id="plot_a_player_tackles",
                    # figure=get_player_tackles("Marco Benassi")
            ),
            dcc.Graph(
                    id="plot_a_player_assists",
            ),
            dcc.Graph(
                #id="plot_player_goals"
                figure=plot_player_goals("Marco Benassi")
            ),

        #categories: "penalties", "saves" and "clean sheets"
            dcc.Graph(
                id="gk_graph",
            )

        ])

app.layout = html.Div([
    # represents the browser address bar and doesn't render anything
    dcc.Location(id='url', refresh=False),
    # content will be rendered in this element
    dcc.Link( html.H1(className="header-description", children='Information Visualization Project'), className="link", href="/"),
    html.Div(id='page-content')
])

if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)