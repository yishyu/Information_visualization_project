import numpy as np
from dash import Dash, html, dcc, Input, Output, callback_context
import plotly.express as px
import pandas as pd
from preprocess import get_all_dataframes
from utils import time_this  # self created utils to time functions
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

# colors: https://plotly.com/python/builtin-colorscales/
TEAMS_COLORS = px.colors.qualitative.Prism

def unify_legend(fig):
    """
        Reduce the legend so that legend icons are only showed once
        and not once per team
    """
    # https://stackoverflow.com/questions/26939121/how-to-avoid-duplicate-legend-labels-in-plotly-or-pass-custom-legend-labels
    names = set()
    fig.for_each_trace(
        lambda trace:
            trace.update(showlegend=False)
            if (trace.name in names) else names.add(trace.name))


@time_this
@app.callback(
    Output('player_dropdown', 'value'),
    Output('player_dropdown', 'options'),
    Input('position_dropdown', 'value'),
    Input('position_dropdown', 'options')
)
def update_dropdowns(position, all_positions):
    """
        Updates the players dropdown depending on the selected position
    """
    if position == "All":
        all_positions.remove(position)  # All is an self added position, it isn't in the database
        players = all_df["info"].sort_values("name")["name"].loc[all_df["info"]["general_position"].isin(all_positions)].unique()
    else:
        players = all_df["info"].sort_values("name")["name"].loc[all_df["info"]["general_position"] == position].unique()
    player = players[0]
    return player, players


@time_this
def get_id_from_name(player_name):
    """
        Utility method to get the id of a player from his name
    """
    ids = all_df["info"]["id"]
    names = all_df["info"]["name"]
    for i in range (0, np.size(names)):
        if names[i] == player_name:
            return ids[i]
    raise ValueError(f"{player_name} is not a valid player")


@time_this
def get_name_from_id(player_id):
    """
        Utility method to get the name of a player from his id
    """
    player_row = all_df["info"].loc[all_df["info"]["id"] == player_id]
    if len(player_row) == 0:
        raise ValueError(f"{player_id} is not a valid player")
    return player_row.iloc[0]["name"]


def get_team_colors(teams):
    """
        Generate a team: color dictionary based on the teams of the player
    """
    team_colors = {}
    for cnt, team in enumerate(teams):
        if not team_colors.get(team):
            team_colors[team] =  TEAMS_COLORS[cnt]
    return team_colors


@time_this
@app.callback(
    Output('plot_player_goals', 'figure'),
    Input('player_dropdown', 'value'),
)
def plot_player_goals(player_name):
    """
        Returns the figure comparing the scored goals with the scoring percentage
        Note: The scoring percentage is defined by the number of goals per shot on target
    """
    player_id = get_id_from_name(player_name)
    try:
        player_df = all_df["shooting"].loc[all_df["shooting"]["id"] == player_id]
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        teams = player_df['squad']
        teams_unique = np.unique(player_df['squad'])
        team_colors = get_team_colors(teams_unique)
        idx_change_of_teams = 0

        for i in range (1, len(teams)+1):  # iterating in all the teams
            if i == len(teams) or teams.iloc[i] != teams.iloc[i-1]:  # whenever the team changes or it's the end of the list
                fig.add_trace(
                    go.Bar(
                        name = f"Goals",
                        x = player_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                        y = player_df.iloc[idx_change_of_teams:i, :]["goals"].tolist(),
                        marker_color = team_colors[teams.iloc[i-1]]
                        ),
                        secondary_y = False,
                )
                fig.add_trace(
                    go.Scatter(
                        x = player_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                        y = player_df.iloc[idx_change_of_teams:i, :]["goals_per_shot_on_target"].tolist(),
                        name = f"Scoring %",
                        marker_color="#000000"
                        ),
                        secondary_y = True,
                )
                idx_change_of_teams = i
        fig.update_xaxes(title_text = "Season", fixedrange=True)  # fixedrange avoid unwanted zooming
        fig.update_yaxes(title_text = "Goals", secondary_y = False, fixedrange=True)
        fig.update_yaxes(title_text = "Percentage", secondary_y = True, fixedrange=True)
        fig.update_layout(
        legend = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor='#f8f9fa',
        barmode="overlay",
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
    """
        Returns the figure showing the amount of yellow & red cards gotten by the player throughout the seasons
    """
    player_id = get_id_from_name(player_name)
    player_misc_df = all_df["misc"].loc[all_df["misc"]["id"] == player_id]

    button_layer_1_height = 1.08
    fig = go.Figure(
        data=[
            go.Bar(name="Red Cards", x=player_misc_df["season"].unique(), y=player_misc_df["cards_red"], marker=dict(color="red"), offsetgroup=0),
            go.Bar(name='Yellow Cards', x=player_misc_df["season"].unique(), y=player_misc_df["cards_yellow"], marker=dict(color="#FFEA00"), offsetgroup=1),
        ],
        layout=go.Layout(
            barmode="group",
            legend = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            title=go.layout.Title(text=f"All cards gotten by {player_name} throughout the seasons"),
            xaxis_title="Seasons",
            yaxis_title="Amount of Cards",
            paper_bgcolor='#f8f9fa',
            font={
                "size": 12,
                "color": "black"
            },
        )
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


@time_this
@app.callback(
    Output('plot_a_player_fouls_cards_seasons', 'figure'),
    Input('player_dropdown', 'value'),
)
def plot_a_player_fouls_cards_seasons(player_name):
    """
        Returns the figure comparing the amount of fouls that the player did and
        the amount of cards that he got
    """
    player_id = get_id_from_name(player_name)
    player_misc_df = all_df["misc"].loc[all_df["misc"]["id"] == player_id]
    player_misc_df["cards"] = player_misc_df["cards_red"] + player_misc_df["cards_yellow"]
    button_layer_1_height = 1.08
    fig = go.Figure(
        data=[
            go.Scatter(name='Cards gotten', x=player_misc_df["season"].unique(), y=player_misc_df["cards"], marker=dict(color="Orange")),
            go.Scatter(name='Number of Fouls', x=player_misc_df["season"].unique(), y=player_misc_df["fouls"], marker=dict(color="#008000")),
        ],
        layout=go.Layout(
            paper_bgcolor='#f8f9fa',
            legend = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            barmode="group",
            title=go.layout.Title(text=f"Amount of faults vs the number of cards for {player_name}"),
            xaxis_title="Seasons",
            yaxis_title="Unity",
            font={
                "size": 12,
                "color": "black"
            },
        )
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


@time_this
@app.callback(
    Output('height', 'children'),
    Output('weight', 'children'),
    Output('position', 'children'),
    Input('player_dropdown', 'value'),
)
def get_player_weight_height(player_name):
    """
        Returns the weight, the height and the specific position of a player
    """
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
    """
        Returns a pie chart showing every club the player has played in during his career
    """
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
    """
        Returns the figure showing the number of games played by a certain player
        and the average minutes he played per game
    """
    player_id = get_id_from_name(player_name)
    try:
        player_df = all_df["playing_time"].loc[all_df["playing_time"]["id"] == player_id]
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        teams = player_df['squad']
        teams_unique = np.unique(player_df['squad'])
        team_colors = get_team_colors(teams_unique)
        idx_change_of_teams = 0

        for i in range (1, len(teams)+1):
            if i == len(teams) or teams.iloc[i] != teams.iloc[i-1]:
                fig.add_trace(
                    go.Bar(
                        name = f"Games played",
                        x = player_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                        y = player_df.iloc[idx_change_of_teams:i, :]["games"].tolist(),
                        marker_color = team_colors[teams.iloc[i-1]]
                        ),
                        secondary_y = False,
                )
                fig.add_trace(
                    go.Scatter(
                        x = player_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                        y = player_df.iloc[idx_change_of_teams:i, :]["minutes_per_game"].tolist(),
                        name = f"Minutes/game",
                        marker_color="#000000"
                        ),
                        secondary_y = True,
                )
                idx_change_of_teams = i
        fig.update_xaxes(title_text = "Season", fixedrange=True)
        fig.update_yaxes(title_text = "Games played", secondary_y = False, fixedrange=True)
        fig.update_yaxes(title_text = "Minutes/game", secondary_y = True, fixedrange=True)
        fig.update_layout(
        legend = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor='#f8f9fa',
        barmode="overlay",
        title=go.layout.Title(text=f"{player_name} games played vs minutes per game"),
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
    Output('plot_a_player_tackles', 'figure'),
    Input('player_dropdown', 'value'),
)
def get_player_tackles(player_name):
    """
        Returns the figure comparing all the tackles of a player
        to the ones that he won
    """
    player_id = get_id_from_name(player_name)
    player_def_df = all_df["defense"].loc[all_df["defense"]["id"] == player_id]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    teams = player_def_df['squad']
    teams_unique = np.unique(player_def_df['squad'])
    team_colors = get_team_colors(teams_unique)
    idx_change_of_teams = 0
    for i in range (1, len(teams)+1):
        if i == len(teams) or teams.iloc[i] != teams.iloc[i-1]:
            fig.add_trace(
                go.Bar(
                    name=f"All tackles",
                    x = player_def_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = player_def_df.iloc[idx_change_of_teams:i, :]["tackles"].tolist(),
                    marker_color = team_colors[teams.iloc[i-1]]
                )
            )
            fig.add_trace(
                go.Scatter(
                    name = f"Won tackles",
                    x = player_def_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = player_def_df.iloc[idx_change_of_teams:i, :]["tackles_won"].tolist(),
                    marker_color="#000000"
                )
            )
            idx_change_of_teams = i
    fig.update_xaxes(title_text = "Season", fixedrange=True)
    fig.update_yaxes(title_text = "Number of Tackles", fixedrange=True)
    fig.update_layout(
        legend = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor='#f8f9fa',
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
    """
        Returns the figure comparing the number of passes of player did
        to the number of assists that he did
    """
    player_id = get_id_from_name(player_name)
    player_pass_df = all_df["passing"].loc[all_df["passing"]["id"] == player_id]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    teams = player_pass_df['squad']
    teams_unique = np.unique(player_pass_df['squad'])
    team_colors = get_team_colors(teams_unique)
    idx_change_of_teams = 0
    for i in range (1, len(teams)+1):
        if i == len(teams) or teams.iloc[i] != teams.iloc[i-1]:
            fig.add_trace(
                go.Bar(
                    name=f"Passes",
                    x = player_pass_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = player_pass_df.iloc[idx_change_of_teams:i, :]["passes"].tolist(),
                    marker_color = team_colors[teams.iloc[i-1]]
                ),secondary_y = False,
            )
            successfull_passes_pct = ((player_pass_df.iloc[idx_change_of_teams:i, :]["passes_pct"])*0.01).tolist()
            fig.add_trace(
                go.Bar(
                    name=f"Successful passes",
                    x = player_pass_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = ((player_pass_df.iloc[idx_change_of_teams:i, :]["passes"])*successfull_passes_pct).tolist(),
                    marker_color = "#b6e880"
                ),secondary_y = False,
            )
            fig.add_trace(
                go.Scatter(
                    name = f"Assists",
                    x = player_pass_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = player_pass_df.iloc[idx_change_of_teams:i, :]["assists"].tolist(),
                    marker_color="#000000"
                ),secondary_y = True,
            )
            idx_change_of_teams = i
    fig.update_xaxes(title_text = "Season", fixedrange=True)
    fig.update_yaxes(title_text = "Number of passes",secondary_y = False, fixedrange=True)
    fig.update_yaxes(title_text = "Number of assists",secondary_y = True, fixedrange=True)
    fig.update_layout(
        paper_bgcolor='#f8f9fa',
        legend = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
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
    """
        Keeper graphs method
        Returns the keeper figure corresponding to the category passed as parameter
    """
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
    teams_unique = np.unique(player_df['squad'])
    team_colors = get_team_colors(teams_unique)
    idx_change_of_teams = 0
    for i in range (1, len(teams)+1):
        if i == len(teams) or teams.iloc[i] != teams.iloc[i-1]:
            fig.add_trace(
                go.Bar(
                    name=f"{yaxes}",
                    x = player_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = player_df.iloc[idx_change_of_teams:i, :][column].tolist(),
                    marker_color = team_colors[teams.iloc[i-1]]
                ),secondary_y = False,
            )
            fig.add_trace(
                go.Scatter(
                    name = f"{yaxes2}",
                    x = player_df.iloc[idx_change_of_teams:i, :]["season"].tolist(),
                    y = player_df.iloc[idx_change_of_teams:i, :][column2].tolist(),
                    marker_color="#000000"
                ),secondary_y = True,
            )
            idx_change_of_teams = i
    fig.update_xaxes(title_text = "Season", fixedrange=True)
    fig.update_yaxes(title_text = yaxes, secondary_y = False, fixedrange=True)
    fig.update_yaxes(title_text = yaxes2, secondary_y = True, fixedrange=True)
    fig.update_layout(
        paper_bgcolor='#f8f9fa',
        legend = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
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
    """
        complementary function for plot_gk in order for the callback to work properly
    """
    return plot_gk(player_name, 'clean sheets')


@time_this
@app.callback(
    Output('plot_saves', 'figure'),
    Input('player_dropdown', 'value')
)
def plot_saves(player_name):
    """
        complementary function for plot_gk in order for the callback to work properly
    """
    return plot_gk(player_name, 'saves')


@time_this
@app.callback(
    Output('plot_penalties', 'figure'),
    Input('player_dropdown', 'value')
)
def plot_penalties(player_name):
    """
        complementary function for plot_gk in order for the callback to work properly
    """
    return plot_gk(player_name, 'penalties')


@app.callback(
    Output('info_graphs', 'style'),
    Output('striker_graphs', 'style'),
    Output('defender_graphs', 'style'),
    Input('graph_type', 'value'),
)
def display_graph(graph_type):
    """
        Returns a css attribute in order to hide or show certain graphs
    """
    no_display = {"display": "none"}
    display = {"display": "flex"}
    if graph_type == "ATT":
        return  display, display, no_display
    elif graph_type == "DEF":
        return  display, no_display, display


def create_card(title, graph_id):
    """
        Creates a card around a graph
    """
    return dbc.Card([
        dbc.CardBody([
            html.H4(f"{title}"),
            dcc.Graph(id=f"{graph_id}", config={'displayModeBar': False, })
        ])
    ], className="mb-4", style={"background-color":"#f8f9fa"})


# modify Pages
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    """
        Handles the url modifications in other terms, the multipage functionality of the platform
        It returns the html objects that will be rendered
    """
    if pathname == "/" :  # Home page with the soccer field
        image_filename = "assets/soccerfield.png"
        # https://community.plotly.com/t/png-image-not-showing/15713
        soccerfield = base64.b64encode(open(image_filename, 'rb').read())  # tricky way to display images without loading an entire assets folder
        return html.Div(children=[
            html.Div([  dcc.Link(html.H1(children='Soccer Statistics', className="header-title"), className="link", href="/"),
            html.H3(children="This website contains statistics about ~3000 (ex)players in the 5 best leagues in Europe.", className="header-description"),
            html.H3(children=[
                "(Spain, Belgium, Germany, France & Italy) ",
                html.A('Dataset Source', href='https://www.kaggle.com/datasets/biniyamyohannes/soccer-player-data-from-fbrefcom', target='_blank')
                ], className="header-description"),
            ], className="header"),
            html.H3(id="select_position_title", children='Select the position you are looking for'),
            html.Div(
                children=[
                    # https://community.plotly.com/t/how-to-embed-images-into-a-dash-app/61839
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
        positions.insert(0, "All")  # adds an "all" category to search between all specific positions
        positions = np.array(positions)
        if position_shortcut == "G":  # the goalkeeper has very specific stats
            gk_graphs = [
                dbc.Row([
                    dbc.Col([create_card("Clean Sheets", "plot_clean_sheets")], width=6),
                    dbc.Col([create_card("Penalties", "plot_penalties")], width=6)
                ]),
                dbc.Row([
                    dbc.Col([create_card("Saves", "plot_saves")], width=12)
                ])
            ]
            graph_type = None
            other_graphs = None
        else:
            values = {"/midfielder": "ATT", "/defender": "DEF", "/striker": "ATT"}
            gk_graphs = None

            # two types of graphs: offensive & defensive
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
                    dbc.Col([create_card("Cards", "plot_a_player_cards_seasons")], width=6),
                    dbc.Col([create_card("Games played", "plot_player_games_played")], width = 6),
                ]),
                dbc.Row(
                    id="defender_graphs",
                    children=[
                     dbc.Col([create_card("Fouls", "plot_a_player_fouls_cards_seasons")], width=6),
                     dbc.Col([create_card("Tackles", "plot_a_player_tackles")], width=6)
                ]),
                dbc.Row(
                    id="striker_graphs",
                    children=[
                    dbc.Col([create_card("Assists", "plot_a_player_assists")], width=6),
                    dbc.Col([create_card("Goals", "plot_player_goals")], width=6)
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
                                config={'displayModeBar': False},
                            ),
                        ], style={"position": "fixed", "bottom":"0", "width":"14%"}
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
    app.run_server(debug=False, threaded=True)