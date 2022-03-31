import pandas as pd
import glob


def get_all_dataframes(path):
    all_df = {}
    for filename in glob.glob(f"{path}*.csv"):
        name = filename.split("/")[1].split(".")[0]
        all_df[name] = pd.read_csv(filename)
    return all_df

def create_new_csv(name, df, columns):
    tmp_df = df[columns]
    tmp_df.to_csv(f"out/{name}.csv", index=False, na_rep='NULL')

def select_columns_from_files():
    all_df = get_all_dataframes("archives/")
    same_columns = ["id", "season", "country", "comp_level", "squad", "age"]
    kept_columns = {
        "info": ["id", "name", "position", "height", "weight", "nt", "countryob", "club", "age"],
        "misc": same_columns + ["cards_yellow", "cards_red", "fouls", "offsides", "interceptions", "tackles_won", "ball_recoveries"],
        "gca": same_columns + ["gca", "gca_per90"],
        "defense": same_columns + ["tackles", "pressures", "dribbled_past", "blocks", "blocked_shots"],
        "keeper": same_columns + ["goals_against_gk", "goals_against_per90_gk", "shots_on_target_against", "save_pct", "clean_sheets", "clean_sheets_pct"],
        "keeper_adv": same_columns + ["passes_gk", "pct_passes_launched_gk"],
        "passing": same_columns + ["passes", "passes_pct", "passes_short", "passes_pct_short", "passes_medium", "passes_pct_medium", "passes_long", "passes_pct_long", "assists"],
        "playing_time": same_columns + ["games", "minutes", "minutes_per_game", "points_per_match"],
        "shooting": same_columns + ["goals", "shots_total", "shots_on_target", "shots_on_target_pct", "goals_per_shot", "goals_per_shot_on_target"],
    }
    for name, columns in kept_columns.items():
        create_new_csv(name, all_df[name], columns)

# keep interesting columns of the file
# select_column_from_files()






