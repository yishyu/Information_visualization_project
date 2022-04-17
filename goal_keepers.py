import numpy as np
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
from preprocess import get_all_dataframes
from utils import time_this
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
def plot_gk(player_name, category):
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

