import pandas as pd
import glob
import platform

def get_all_dataframes(path):
    os_char = {'Linux': '/', 'Darwin': '/', 'Windows': '\\'}
    all_df = {}
    for filename in glob.glob(f"{path}*.csv"):
        name = filename.split(os_char[platform.system()])[1].split(".")[0]
        all_df[name] = pd.read_csv(filename)
    return all_df

def create_new_csv(name, df, columns):
    tmp_df = df[columns]
    tmp_df.to_csv(f"out/{name}.csv", index=False, na_rep='NULL')


def split_position(position):
    if '(' in position:
        return position.split('(')[0].strip()
    else:
        return position


def select_columns_from_files():
    all_df = get_all_dataframes("archives/")
    same_columns = ["id", "season", "country", "comp_level", "squad", "age"]
    kept_columns = {
        "info": ["id", "name", "general_position", "position", "height", "weight", "nt", "countryob", "club", "age"],
        "misc": same_columns + ["cards_yellow", "cards_red", "fouls", "offsides", "interceptions", "tackles_won", "ball_recoveries"],
        "defense": same_columns + ["tackles", "pressures", "dribbled_past", "blocks", "blocked_shots", "pressure_regain_pct", "tackles_won"],
        "keeper": same_columns + ["goals_against_gk", "goals_against_per90_gk", "shots_on_target_against", "save_pct", "clean_sheets", "clean_sheets_pct", "pens_att_gk", "pens_missed_gk", "pens_save_pct"],
        "passing": same_columns + ["passes", "passes_pct", "passes_short", "passes_pct_short", "passes_medium", "passes_pct_medium", "passes_long", "passes_pct_long", "assists"],
        "playing_time": same_columns + ["games", "minutes", "minutes_per_game", "points_per_match"],
        "shooting": same_columns + ["goals", "shots_total", "shots_on_target", "shots_on_target_pct", "goals_per_shot", "goals_per_shot_on_target"],
    }

    for name, columns in kept_columns.items():
        if name == "info":
            all_df[name]["general_position"] = all_df[name]["position"].apply(split_position)
        create_new_csv(name, all_df[name], columns)

if __name__ == "__main__":
    # keep interesting columns of the file
    select_columns_from_files()






