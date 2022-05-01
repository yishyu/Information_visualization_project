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
import random


app = Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

all_df = get_all_dataframes("out/")

TEAMS_COLORS = {}

# Generate all the colors based on all available teams
def generate_color(column):
    for value in column.unique():
        if not TEAMS_COLORS.get(value, None):
            color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            while color in TEAMS_COLORS.values():
                color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            TEAMS_COLORS[value] = color
def map_color(team):
    return TEAMS_COLORS[team]

def unify_legend(fig):
    # https://stackoverflow.com/questions/26939121/how-to-avoid-duplicate-legend-labels-in-plotly-or-pass-custom-legend-labels
    names = set()
    fig.for_each_trace(
        lambda trace:
            trace.update(showlegend=False)
            if (trace.name in names) else names.add(trace.name))
@time_this
@app.callback(
    # Output('position_dropdown', 'value'),
    # Output('position_dropdown', 'options'),
    Output('player_dropdown', 'value'),
    Output('player_dropdown', 'options'),
    Input('position_dropdown', 'value'),
    Input('position_dropdown', 'options'),
)
def update_dropdowns(position, all_positions):
    if position == "All":
        all_positions.remove(position)
        players = all_df["info"].sort_values("name")["name"].loc[all_df["info"]["position"].isin(all_positions)].unique()
    else:
        players = all_df["info"].sort_values("name")["name"].loc[all_df["info"]["position"] == position].unique()
    player = players[0]
    return player, players


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
        go.Pie(labels=values.index.tolist(), values=values.tolist(), textinfo='label+percent', marker_colors=list(map(map_color, values.index.tolist())))
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
    player_df = all_df["playing_time"].loc[all_df["playing_time"]["id"] == player_id].sort_values('season')
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    teams = player_df['squad']
    # for the games played (bar plot)
    idx_change_of_teams = 0
    for i in range (1, len(teams)+1):
        if i == len(teams) or teams.iloc[i] != teams.iloc[i-1]:
            fig.add_trace(
                go.Bar(
                    name = f"Games played for {teams.iloc[idx_change_of_teams]}",
                    x = player_df.iloc[idx_change_of_teams:i, :]["season"].tolist(), # [player_df['season'][j] for j in range(idx_change_of_teams,i)],
                    y = player_df.iloc[idx_change_of_teams:i, :]["games"].tolist(), # [player_df['games'][j] for j in range(idx_change_of_teams,i)]),
                    marker_color=TEAMS_COLORS[teams.iloc[idx_change_of_teams]]

                ),secondary_y = False,

            )
            fig.add_trace(
                go.Scatter(
                    name = f"Minutes per game for {teams.iloc[idx_change_of_teams]}",
                    x = player_df.iloc[idx_change_of_teams:i, :]["season"].tolist(), # [player_df['season'][j] for j in range(idx_change_of_teams,i)],
                    y = player_df.iloc[idx_change_of_teams:i, :]["minutes_per_game"].tolist(), # [player_df['games'][j] for j in range(idx_change_of_teams,i)]),
                    marker_color="#000000"

                ),secondary_y = True,

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
    unify_legend(fig)
    return fig

@time_this
@app.callback(
    Output('plot_a_player_tackles', 'figure'),
    Input('player_dropdown', 'value'),
)
def get_player_tackles(player_name):
    player_id = get_id_from_name(player_name)
    player_def_df = all_df["defense"].loc[all_df["defense"]["id"] == player_id]

    fig = go.Figure()
    teams = player_def_df['squad']

    idx_change_of_teams = 0
    for i in range (1, len(teams)+1):
        if i == len(teams) or teams.iloc[i] != teams.iloc[i-1]:
            fig.add_trace(
                go.Bar(
                    name = f"won tackles for {teams.iloc[idx_change_of_teams]}",
                    x = player_def_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = player_def_df.iloc[idx_change_of_teams:i, :]["tackles_won"].tolist(),
                    marker_color=TEAMS_COLORS[teams.iloc[idx_change_of_teams]]
                )
            )
            fig.add_trace(
                    go.Bar(
                        name=f"all tackles for {teams.iloc[idx_change_of_teams]}",
                        x = player_def_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                        y = player_def_df.iloc[idx_change_of_teams:i, :]["tackles"].tolist(),
                        marker_color=TEAMS_COLORS[teams.iloc[idx_change_of_teams]]
                    )
            )
            idx_change_of_teams = i
    fig.update_xaxes(title_text = "season")
    fig.update_yaxes(title_text = "Number of Tackles")
    fig.update_layout(
        title=go.layout.Title(text=f"{player_name} all tackles vs won tackles"),
        font={
                "size": 12,
                "color": "black"
            },
    )
    unify_legend(fig)
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


# modify Pages
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
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

        position_shortcuts = {"/midfielder": "M", "/keeper": "G", "/defender": "D", "/striker": "A|F"}
        position_text = {"/midfielder": "Midfielders", "/keeper": "Goal Keepers", "/defender": "Defenders", "/striker": "Strikers"}
        position_shortcut = position_shortcuts[pathname]
        positions = all_df["info"].loc[all_df["info"]["position"].str.contains(position_shortcut)].sort_values("position")["position"].unique().tolist()
        positions.insert(0, "All")
        positions = np.array(positions)
        return html.Div(children=[
            html.H2(children=f'Soccer Statistics : {position_text[pathname]}'),
            html.Div(
                className="row",
                children=[
                    html.Div( ## Date select dcc components
                        id='div_position_dd',
                        children=
                        [
                            dcc.Markdown("Choose a specific field position"),
                            dcc.Dropdown(
                                positions,
                                positions[0],
                                id='position_dropdown',
                                placeholder="Select a field position"
                            ),
                        ],
                    ),
                    html.Div( ## Stock select
                    id="div_choose_player_dd",
                    children=
                    [
                        dcc.Markdown("Choose a Player"),
                        dcc.Dropdown(
                            id='player_dropdown',
                            placeholder="Select a player"
                        ),
                    ],
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
    html.Div([  dcc.Link(html.H1(children='Soccer Statistics', className="header-title"), className="link", href="/"),
                html.H3(children="This website contains statistics about ~3000 (ex)players in the 5 best leagues in Europe.", className="header-description"),
                html.H3(children="(Spain, Belgium, Germany, France & Italy)", className="header-description"),
                ], className="header"),
    html.Div(id='page-content'),
])

if __name__ == '__main__':
    generate_color(all_df["info"]["club"])
    for name, df in all_df.items():
        if name != 'info':
            generate_color(df["squad"])
    app.run_server(debug=True, threaded=True)