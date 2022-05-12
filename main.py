import numpy as np
from dash import Dash, html, dcc, Input, Output, callback_context
import plotly.express as px
import pandas as pd
from preprocess import get_all_dataframes
from utils import time_this
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import base64
import random
import dash_bootstrap_components as dbc


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

all_df = get_all_dataframes("out/")

# colors: https://plotly.com/python/discrete-color/
TEAMS_COLORS = [
    '#1f77b4',  # muted blue
    '#ff7f0e',  # safety orange
    '#2ca02c',  # cooked asparagus green
    '#d62728',  # brick red
    '#9467bd',  # muted purple
    '#8c564b',  # chestnut brown
    '#e377c2',  # raspberry yogurt pink
    '#7f7f7f',  # middle gray
    '#bcbd22',  # curry yellow-green
    '#17becf'   # blue-teal
]


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
        players = all_df["info"].sort_values("name")["name"].loc[all_df["info"]["general_position"].isin(all_positions)].unique()
    else:
        players = all_df["info"].sort_values("name")["name"].loc[all_df["info"]["general_position"] == position].unique()
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
@app.callback(
    Output('plot_player_goals', 'figure'),
    Input('player_dropdown', 'value'),
)
def plot_player_goals(player_name):
    player_id = get_id_from_name(player_name)
    try:
        player_df = all_df["shooting"].loc[all_df["shooting"]["id"] == player_id]
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        teams = player_df['squad']
        team_colors = {}
        counter = 0
        team_nr = 0
        idx_change_of_teams = 0
        for i in range (1, len(teams)+1):
            if i == len(teams) or teams.iloc[i] != teams.iloc[i-1]:
                if (not(teams.iloc[counter] in list(team_colors.keys()))):
                    team_colors[teams.iloc[counter]] =  TEAMS_COLORS[team_nr]
                fig.add_trace(
                    go.Bar(
                        name = f"Goals for {teams.iloc[idx_change_of_teams]}",
                        x = player_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                        y = player_df.iloc[idx_change_of_teams:i, :]["goals"].tolist(),
                        marker_color = team_colors[teams.iloc[counter]]
                        ),
                        secondary_y = False,
                )
                fig.add_trace(
                    go.Scatter(
                        x = player_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                        y = player_df.iloc[idx_change_of_teams:i, :]["goals_per_shot_on_target"].tolist(),
                        name = f"Scoring % for {teams.iloc[idx_change_of_teams]}",
                        marker_color="#000000"
                        ),
                        secondary_y = True,
                )
                idx_change_of_teams = i
                team_nr = team_nr + 1
            counter = counter + 1
        fig.update_xaxes(title_text = "season")
        fig.update_yaxes(title_text = "goals", secondary_y = False)
        fig.update_yaxes(title_text = "percentage", secondary_y = True)
        fig.update_layout(
        title=go.layout.Title(text=f"{player_name} scored goals vs scoring percentage"),
        font={
                "size": 12,
                "color": "black"
            },
    )
    except:
        fig = go.Figure()
    unify_legend(fig)
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
            title=go.layout.Title(text=f"All cards gotten by {player_name} throughout the seasons"),
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
            go.Scatter(name='Cards gotten', x=player_misc_df["season"].unique(), y=player_misc_df["cards"], marker=dict(color="Orange")),
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
    Output('position', 'children'),
    Input('player_dropdown', 'value'),
)
def get_player_weight_height(player_name):
    player_row = all_df["info"].loc[all_df['info']['name'] == player_name]
    height = player_row.iloc[0]["height"]
    weight = player_row.iloc[0]["weight"]
    position = player_row.iloc[0]['position']
    return f"Height: {height} cm", f"Weight: {weight} kg", f"Position: {position}"

@time_this
@app.callback(
    Output('plot_a_player_clubs_seasons', 'figure'),
    Input('player_dropdown', 'value'),
)
def get_player_club_evolution(player_name):
    player_id = get_id_from_name(player_name)
    player_misc_df = all_df["misc"].loc[all_df["misc"]["id"] == player_id]
    figure = go.Figure()
    unique_teams = np.unique(player_misc_df["squad"], return_counts = True)
    teams = player_misc_df["squad"]
    figure.add_trace(
        go.Pie(
            labels=unique_teams[0],
            values=unique_teams[1],
            textinfo='label+percent',
            marker=dict(colors=[TEAMS_COLORS[i] for i in range(0, len(unique_teams[0]))])
        )
    )
    figure.update_layout(
        paper_bgcolor='#f8f9fa',
        showlegend=False,
        height=300,
        font={
                "size": 12,
                "color": "black"
            },
        margin=dict(t=0, b=0, l=10, r=10)
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
    team_colors = {}
    counter = 0
    team_nr = 0
    idx_change_of_teams = 0
    for i in range (1, len(teams)+1):
        if i == len(teams) or teams.iloc[i] != teams.iloc[i-1]:
            if (not(teams.iloc[counter] in list(team_colors.keys()))):
                    team_colors[teams.iloc[counter]] =  TEAMS_COLORS[team_nr]
            fig.add_trace(
                go.Bar(
                    name = f"Games played for {teams.iloc[idx_change_of_teams]}",
                    x = player_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = player_df.iloc[idx_change_of_teams:i, :]["games"].tolist(),
                    marker_color = team_colors[teams.iloc[counter]]

                ),secondary_y = False,

            )
            fig.add_trace(
                go.Scatter(
                    name = f"Minutes/game for {teams.iloc[idx_change_of_teams]}",
                    #textfont = 9,
                    x = player_df.iloc[idx_change_of_teams:i, :]["season"].tolist(), 
                    y = player_df.iloc[idx_change_of_teams:i, :]["minutes_per_game"].tolist(),
                    marker_color="#000000"

                ),secondary_y = True,

            )
            idx_change_of_teams = i
            team_nr = team_nr + 1
        counter = counter + 1
    fig.update_xaxes(title_text = "season")
    fig.update_yaxes(title_text = "games", secondary_y = False)
    fig.update_yaxes(title_text = "minutes", secondary_y = True)
    fig.update_layout(
        barmode="overlay",
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

    #fig = go.Figure()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    teams = player_def_df['squad']
    team_colors = {}
    counter = 0
    team_nr = 0
    idx_change_of_teams = 0
    for i in range (1, len(teams)+1):
        if i == len(teams) or teams.iloc[i] != teams.iloc[i-1]:
            if (not(teams.iloc[counter] in list(team_colors.keys()))):
                    team_colors[teams.iloc[counter]] =  TEAMS_COLORS[team_nr]
            fig.add_trace(
                go.Bar(
                    name=f"All tackles for {teams.iloc[idx_change_of_teams]}",
                    x = player_def_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = player_def_df.iloc[idx_change_of_teams:i, :]["tackles"].tolist(),
                    marker_color = team_colors[teams.iloc[counter]]
                )#,secondary_y = False,
            )
            fig.add_trace(
                go.Scatter(
                    name = f"Won tackles for {teams.iloc[idx_change_of_teams]}",
                    x = player_def_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = player_def_df.iloc[idx_change_of_teams:i, :]["tackles_won"].tolist(),
                    marker_color="#000000"
                )#,secondary_y = True,
            )
            idx_change_of_teams = i
            team_nr = team_nr + 1
        counter = counter + 1
    fig.update_xaxes(title_text = "season")
    fig.update_yaxes(title_text = "Number of Tackles")
    #fig.update_yaxes(title_text = "Number of Tackles won",secondary_y = True)
    fig.update_layout(
        barmode="overlay",
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
    player_pass_df = all_df["passing"].loc[all_df["passing"]["id"] == player_id]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    teams = player_pass_df['squad']
    team_colors = {}
    counter = 0
    team_nr = 0
    idx_change_of_teams = 0
    for i in range (1, len(teams)+1):
        if i == len(teams) or teams.iloc[i] != teams.iloc[i-1]:
            if (not(teams.iloc[counter] in list(team_colors.keys()))):
                    team_colors[teams.iloc[counter]] =  TEAMS_COLORS[team_nr]
            fig.add_trace(
                go.Bar(
                    name=f"Passes for {teams.iloc[idx_change_of_teams]}",
                    x = player_pass_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = player_pass_df.iloc[idx_change_of_teams:i, :]["passes"].tolist(),
                    marker_color = team_colors[teams.iloc[counter]]
                ),secondary_y = False,
            )
            successfull_passes_pct = ((player_pass_df.iloc[idx_change_of_teams:i, :]["passes_pct"])*0.01).tolist()
            fig.add_trace(
                go.Bar(
                    name=f"Successful passes for {teams.iloc[idx_change_of_teams]}",
                    x = player_pass_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = ((player_pass_df.iloc[idx_change_of_teams:i, :]["passes"])*successfull_passes_pct).tolist(),
                    marker_color = "#16ff32"
                ),secondary_y = False,
            )
            fig.add_trace(
                go.Scatter(
                    name = f"assists for {teams.iloc[idx_change_of_teams]}",
                    x = player_pass_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = player_pass_df.iloc[idx_change_of_teams:i, :]["assists"].tolist(),
                    marker_color="#000000"
                ),secondary_y = True,
            )
            idx_change_of_teams = i
            team_nr = team_nr + 1
        counter = counter + 1
    fig.update_xaxes(title_text = "season")
    fig.update_yaxes(title_text = "Number of passes",secondary_y = False)
    fig.update_yaxes(title_text = "Number of assists",secondary_y = True)
    fig.update_layout(
        barmode="overlay",
        title=go.layout.Title(text=f"{player_name} successful passes vs assists"),
        font={
                "size": 12,
                "color": "black"
            },
    )
    unify_legend(fig)
    return fig


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

    teams = player_df['squad']
    team_colors = {}
    counter = 0
    team_nr = 0
    idx_change_of_teams = 0
    for i in range (1, len(teams)+1):
        if i == len(teams) or teams.iloc[i] != teams.iloc[i-1]:
            if (not(teams.iloc[counter] in list(team_colors.keys()))):
                    team_colors[teams.iloc[counter]] =  TEAMS_COLORS[team_nr]
            fig.add_trace(
                go.Bar(
                    name=f"{yaxes} for {teams.iloc[idx_change_of_teams]}",
                    x = player_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = player_df.iloc[idx_change_of_teams:i, :][column].tolist(),
                    marker_color = team_colors[teams.iloc[counter]]
                ),secondary_y = False,
            )
            fig.add_trace(
                go.Scatter(
                    name = f"{yaxes2} for {teams.iloc[idx_change_of_teams]}",
                    x = player_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = player_df.iloc[idx_change_of_teams:i, :][column2].tolist(),
                    marker_color="#000000"
                ),secondary_y = True,
            )
            idx_change_of_teams = i
            team_nr = team_nr + 1
        counter = counter + 1
    fig.update_xaxes(title_text = "season")
    fig.update_yaxes(title_text = yaxes, secondary_y = False)
    fig.update_yaxes(title_text = yaxes2, secondary_y = True)
    fig.update_layout(
        barmode="overlay",
        title=go.layout.Title(text=f"{player_name} {yaxes} vs {yaxes2}"),
        font={
                "size": 12,
                "color": "black"
            },
    )
    unify_legend(fig)
    return fig

@time_this
@app.callback(
    Output('plot_clean_sheets', 'figure'),
    Input('player_dropdown', 'value')
)
def plot_clean_sheets(player_name):
    return plot_gk(player_name, 'clean sheets')


@time_this
@app.callback(
    Output('plot_saves', 'figure'),
    Input('player_dropdown', 'value')
)
def plot_saves(player_name):
    return plot_gk(player_name, 'saves')


@time_this
@app.callback(
    Output('plot_penalties', 'figure'),
    Input('player_dropdown', 'value')
)
def plot_penalties(player_name):
    return plot_gk(player_name, 'penalties')

@app.callback(
    # Output('plot_a_player_fouls_cards_seasons', 'style'),
    # Output('plot_a_player_tackles', 'style'),



    Output('info_graphs', 'style'),
    Output('striker_graphs', 'style'),
    Output('defender_graphs', 'style'),
    #Output('plot_a_player_cards_seasons', 'style'),


    Input('graph_type', 'value'),
)
def display_graph(graph_type):
    no_display = {"display": "none"}
    display = {"display": "flex"}
    # plot_player_games_played, plot_a_player_cards_seasons, plot_a_player_assists, plot_player_goals, plot_a_player_tackles, plot_a_player_fouls_cards_seasons
    if graph_type == "ATT":
        return  display, display, no_display
    elif graph_type == "DEF":
        return  display, no_display, display


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
            html.Div([  dcc.Link(html.H1(children='Soccer Statistics', className="header-title"), className="link", href="/"),
            html.H3(children="This website contains statistics about ~3000 (ex)players in the 5 best leagues in Europe.", className="header-description"),
            html.H3(children="(Spain, Belgium, Germany, France & Italy)", className="header-description"),
            ], className="header"),
            html.H3(id="select_position_title", children='Select the position you are looking for'),
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

        position_shortcuts = {"/midfielder": "M", "/keeper": "G", "/defender": "D", "/striker": "A|FW"}
        position_text = {"/midfielder": "Midfielders", "/keeper": "Goal Keepers", "/defender": "Defenders", "/striker": "Strikers"}
        position_shortcut = position_shortcuts[pathname]
        positions = all_df["info"].loc[all_df["info"]["general_position"].str.contains(position_shortcut)].sort_values("general_position")["general_position"].unique().tolist()
        positions.insert(0, "All")
        positions = np.array(positions)
        if position_shortcut == "G":  # the goalkeeper has very specific stats
            gk_graphs = [
                dbc.Row([
                    dbc.Col([dcc.Graph (id="plot_clean_sheets", config={'displayModeBar': False})], width=6),
                    dbc.Col([dcc.Graph (id="plot_penalties", config={'displayModeBar': False})], width=6)
                ]),
                dbc.Row([
                    dbc.Col([dcc.Graph (id="plot_saves", config={'displayModeBar': False})], width=12)
                ])
            ]
            graph_type = None
            other_graphs = None
        else:
            values = {"/midfielder": "ATT", "/defender": "DEF", "/striker": "ATT"}
            gk_graphs = None


            graph_type = dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4("Graph types"),
                                    html.Div([
                                        dcc.RadioItems(
                                        id="graph_type",
                                        options = {
                                            'ATT': ' Offensive Stats',
                                            'DEF': ' Defensive Stats ',
                                        },
                                        value = values[pathname],
                                        labelStyle={'display': 'block', "margin-bottom": "1rem"},
                                    )
                                    ])
                                ]
                            )
                        ],
                        style={"margin-top": "1rem", "margin-bottom": "5%"}
                    )
            other_graphs = [
                dbc.Row(
                    id="info_graphs",
                    children=[
                    dbc.Col([dcc.Graph(id="plot_a_player_cards_seasons", config={'displayModeBar': False})], width=6),
                    dbc.Col([dcc.Graph(id="plot_player_games_played", config={'displayModeBar': False})], width=6)
                ]),
                dbc.Row(
                    id="defender_graphs",
                    children=[
                     dbc.Col([dcc.Graph(id="plot_a_player_fouls_cards_seasons", config={'displayModeBar': False})], width=6),
                     dbc.Col([dcc.Graph(id="plot_a_player_tackles", config={'displayModeBar': False})], width=6)
                ]),
                dbc.Row(
                    id="striker_graphs",
                    children=[
                    dbc.Col([dcc.Graph(id="plot_a_player_assists", config={'displayModeBar': False})], width=6),
                    dbc.Col([dcc.Graph(id="plot_player_goals", config={'displayModeBar': False})], width=6)
                ])
            ]
        return html.Div(children=[
            html.Div([

                dcc.Link(
                    [
                        html.I(className="bi bi-house-door-fill fa-8x", style={"margin-left":"2%", "font-size": "30px", "color":"white"}),
                        html.H1(children='Soccer Statistics', className="header-title")
                    ], className="link d-flex align-items-center", href="/")
            ], className="second_header"),
            # sidebar
            html.Div(
                [
                    html.H3(f"{position_text[pathname]}"),
                    html.Hr(),
                    html.Div( ## Date select dcc components
                        id='div_position_dd',
                        children=
                        [
                            html.P("Choose a specific field position"),
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
                        style={"margin-top": "1rem"}
                    ),

                    html.Div(children=[
                        html.Span(id="height"),
                    ], style={"margin-top": "1rem"}),

                    html.Div(children=[
                        html.Span(id="weight"),
                    ], style={"margin-top": "1rem"}),

                    html.Div(children=[
                        html.Span(id="position"),
                    ], style={"margin-top": "1rem"}),

                    graph_type,
                    html.Div(
                        [
                            html.H5(f"Clubs"),
                            dcc.Graph(
                                id="plot_a_player_clubs_seasons",

                                config={'displayModeBar': False}
                            ),
                        ], style={"position": "fixed", "bottom":"0", "width":"14%",}
                    ),

                ], className="sidebar"
            ),
            html.Div([
                html.Div(children=other_graphs),
                #categories: "penalties", "saves" and "clean sheets"
                html.Div(children=gk_graphs),
            ], className="content")
        ])


app.title = "Soccer Statistics"
app.layout = html.Div([
    # represents the browser address bar and doesn't render anything
    dcc.Location(id='url', refresh=False),

    # content will be rendered in this element

    html.Div(id='page-content'),
])

if __name__ == '__main__':
    # generate_color(all_df["info"]["club"])
    # for name, df in all_df.items():
    #     if name != 'info':
    #         generate_color(df["squad"])
    app.run_server(debug=False, threaded=True)