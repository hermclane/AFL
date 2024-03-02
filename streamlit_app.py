import streamlit as st
import pandas as pd
from PIL import Image
from datetime import datetime
import matplotlib as plt
from github import Github
import io
from io import BytesIO
import requests
import os
from dotenv import load_dotenv
import altair as alt
import base64

# CHANGE ROUND EVERY WEEK
CURRENT_ROUND = 0
CURRENT_YEAR = 2024

# HIDE ACCESS KEY
load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
g = Github(st.secrets.clientid.clientid, st.secrets.clientsecret.clientsecret)
# g = Github(GITHUB_TOKEN)

GITHUB_TOKEN2 = os.getenv('GITHUB_TOKEN2')
g2 = Github(st.secrets.privaterepo.privaterepo)
# g2 = Github(GITHUB_TOKEN2)


st.set_page_config(page_title="Unseen Stats",
                   page_icon="🔮",
                   layout='wide')


@st.cache_resource
def open_repo():
    repo = g.get_repo('hermclane/AFL')
    return repo

@st.cache_resource
def open_private_repo():
    private_repo = g2.get_repo('hermclane/AFLPlayerStatsRepo')
    return private_repo


repo = open_repo()
private_repo = open_private_repo()


@st.cache_data
def read_fixture():
    # load fixture data once
    fixture_df = pd.read_excel(r"https://raw.githubusercontent.com/hermclane/AFL/main/AFLFixtures2024.xlsx")
    return fixture_df

# Make Dataframes
fixture_df = read_fixture()
current_round_fixture_df = fixture_df[fixture_df["Round Number"] == CURRENT_ROUND]

# Get the list of match strings from the "Match String" column of the current_round_fixture_df DataFrame
match_list = current_round_fixture_df["Match String"].tolist()

parent_folder_path = f"Round_{CURRENT_ROUND}"

#Load Current Round Folder Contents
@st.cache_data
def get_parent_folder_contents():
    # load parent folder contents once
    parent_folder_contents = repo.get_contents(parent_folder_path)
    return parent_folder_contents

parent_folder_contents = get_parent_folder_contents()

folder_list = [content.name for content in parent_folder_contents if content.type == 'dir']

sorted_folder_list = [folder_name for match_str in match_list for folder_name in folder_list if match_str in folder_name]

@st.cache_data
def get_private_repo_contents():
    private_repo_contents = private_repo.get_contents("")
    return private_repo_contents

private_repo_contents = get_private_repo_contents()

private_folder_list = [content.name for content in private_repo_contents if content.type == 'dir']

@st.cache_data
def get_players_df():
    for file in private_repo.get_contents(""):
        if file.name == 'AFLPlayers2024.xlsx':
            excel_data = BytesIO(base64.b64decode(file.content))
            players_df = pd.read_excel(excel_data, engine='openpyxl')
            return players_df

players_df = get_players_df()

@st.cache_data
def get_previous_H2H_games(_repo, parent_folder_path):
    previous_H2H_csv = None
    for file in repo.get_contents(parent_folder_path):
        if file.name.endswith('H2H Results.csv'):
            file_content = file.decoded_content
            previous_H2H_csv = pd.read_csv(BytesIO(file_content))
            break
    return previous_H2H_csv

previous_H2H_csv = get_previous_H2H_games(repo, parent_folder_path)

# Parse and format Last H2H Encounter results
def parse_team_H2H_data(team, previous_H2H_csv, is_home_team):
    mapping_dic = {"Win": "✔️", "Draw": "➖", "Lose": "❌"}
    if is_home_team:
        current_team_H2H = previous_H2H_csv[previous_H2H_csv["Home Team"] == team]
        current_team_H2H_results_list = current_team_H2H["Home Team Outcome"].to_list()
        current_team_H2H_results_list = [mapping_dic[result] for result in current_team_H2H_results_list]
    if not is_home_team:
        current_team_H2H = previous_H2H_csv[previous_H2H_csv["Away Team"] == team]
        current_team_H2H_results_list = current_team_H2H["Away Team Outcome"].to_list()
        current_team_H2H_results_list = [mapping_dic[result] for result in current_team_H2H_results_list]

    current_team_H2H_results_string =''.join(current_team_H2H_results_list)

    return current_team_H2H_results_string


# Load Logo
@st.cache_data
def get_logo():
    image_url = 'https://raw.githubusercontent.com/hermclane/AFL/main/Logo.png'
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    return image


# Set Logo
image = get_logo()
st.sidebar.image(image, use_column_width=True)

# Set the title of the sidebar
st.sidebar.title(f'Current Round: {CURRENT_ROUND}')

# Create an empty dictionary to store the folder names and corresponding team string
folder_team_dict = {}

selected_folder_name = st.sidebar.radio('Select a game (Home Team vs Away Team):', sorted_folder_list)
selected_folder_path = f"{parent_folder_path}/{selected_folder_name}"


@st.cache_data
def get_selected_folder_contents():
    # load chosen game contents once
    selected_folder_contents = repo.get_contents(selected_folder_path)
    return selected_folder_contents


selected_folder_contents = get_selected_folder_contents()

csv_list = [file.name for file in selected_folder_contents if file.name.endswith('.csv')]

# Check if the folder name matches the "Folder url" column of the "current_round_fixture_df"
matching_row = current_round_fixture_df[current_round_fixture_df["Match String"] == selected_folder_name]
home_team = matching_row["Home Team"].iloc[0]
away_team = matching_row["Away Team"].iloc[0]
home_team_url = matching_row["Home Team url"].iloc[0]
away_team_url = matching_row["Away Team url"].iloc[0]

# Format and Set page Header
# Create Date and time for header display
game_datetime_np = current_round_fixture_df.loc[current_round_fixture_df['Match String'] == selected_folder_name, 'Date'].values[0]
game_datetime_str = game_datetime_np.astype(str)
game_datetime_obj = datetime.strptime(game_datetime_str[:-3], '%Y-%m-%dT%H:%M:%S.%f')
game_day_time_str = game_datetime_obj.strftime('%A, %I:%M %p')
# Get venue for header display
location = current_round_fixture_df.loc[current_round_fixture_df['Match String'] == selected_folder_name, 'Location'].values[0]
# Configure Game Header
header_display = f'{selected_folder_name} - {location} - {game_day_time_str} AEST'


# Define Colourmap
colors = [(0, 0, 0, 0), "#488f31"]
# Create the colourmap
cmap = plt.colors.LinearSegmentedColormap.from_list("custom_cmap", colors)


# Load Game Averages CSV Data
@st.cache_data
def load_csv_data(_repo, selected_folder_path):
    csv_dict = {}
    for file in repo.get_contents(selected_folder_path):
        if file.name.endswith('Average.csv'):
            df = pd.read_csv(io.StringIO(file.decoded_content.decode('utf-8')))
            csv_dict[file.name.replace('.csv', '')] = df
    return csv_dict

# Load CSV data into a dictionary
csv_dict = load_csv_data(repo, selected_folder_path)


# Read all H2H Games CSV Data
@st.cache_data
def load_player_H2H_data(_repo, selected_folder_path):
    csv_dict_H2H = {}  # Dictionary to store each DataFrame

    for file in repo.get_contents(selected_folder_path):
        if file.name.endswith('H2H Games.csv'):
            file_content = file.decoded_content
            df = pd.read_csv(BytesIO(file_content), parse_dates=['Date'], dayfirst=True)

            # Remove '.csv' from filename for the dictionary key
            dict_key = file.name.replace(' H2H Games.csv', '')  # Adjusted to use file.name
            csv_dict_H2H[dict_key] = df

    return csv_dict_H2H


csv_dict_H2H = load_player_H2H_data(repo, selected_folder_path)

styled_columns = ["Player","Total Games Played", "Highest Dis.", "Lowest Dis.", "Disposals", "Goals", "Behinds",
                  "Frees For", "15 Dis. %", "20 Dis. %", "25 Dis. %", "1 Goal %", "2 Goals %"]

drop_columns_2024 = ["Team", "Home/Away", "M", "T", "K", "HB", "HO", "GA", "I50", "CL", "CG", "R50", "FF", "FA", "AF", "SC"]

# Exclude for colour map
exclude_columns_cmap = ['Round', 'Opponent', 'Result', 'Player Name', "Date", "DisplayRound"]

# Columns that are required but need to be excluded from final display
exclude_columns = ['DisplayRound', 'Date']

dummy_columns = ["Player Name", "Round", "Opponent", "Result", "D", "G", "B", "DisplayRound", "Date"]

finals_round_mapping = {
    'Elimination Final': 'EF',
    "Preliminary Final": "PF",
    "Preliminary Finals": "PF",
    "Grand Final": "GF",
    "Qualifying Final": "QF",
    "Semi Finals": "SF",
    "Semi Final": "SF"
}

# Generate round names for 0 to 24
round_names = [str(i) for i in range(0, 25)]
# Append special rounds
special_rounds = ['EF', 'QF', 'PF', 'SF', 'GF']
round_names.extend(special_rounds)

# Display Header
st.header(header_display)

# Selectbox to choose Averages to display
chosen_type = st.selectbox("Game Averages", ("Season Average", "Last 10 Average", "Last 5 Average", "Last 3 Average"))

home_team_tab, away_team_tab = st.tabs([f'Home: {home_team}', f'Away: {away_team}'])

# Display each CSV file as a table
for csv_name, csv_df in csv_dict.items():
    if chosen_type in csv_name:
        with home_team_tab:
            if home_team in csv_name:
                #Load Headers and H2H Data
                parsed_H2H_Team_data_string = parse_team_H2H_data(home_team, previous_H2H_csv, True)
                st.subheader(f"Previous H2H vs {away_team}: {parsed_H2H_Team_data_string}")
                st.subheader(csv_name)
                # Load Home Team DF
                df = csv_df.sort_values(by=['Disposals'], ascending=False)

                # Create columns for layout
                col1, col2 = st.columns([1, 6])

                # Sort player names alphabetically and create st.radio in the first column for player select
                with col1:
                    sorted_players_home = sorted(df['Player'].unique())
                    selected_player_home = st.radio("Select a Player", sorted_players_home)
                    selected_player_home_url = players_df.loc[players_df['Player'] == selected_player_home, 'name_url'].iloc[0]

                current_player_home_chosen_average_df = df[df["Player"] == selected_player_home]
                current_player_home_chosen_average_disposals = current_player_home_chosen_average_df["Disposals"].iloc[0]
                current_player_home_chosen_average_goals = current_player_home_chosen_average_df["Goals"].iloc[0]

                # Display the DataFrame in the second column
                with col2:
                    st.dataframe(df[styled_columns].style.format({"Disposals": "{:.2f}", "Goals": "{:.2f}",
                                                                  "Behinds": "{:.2f}", "Frees For": "{:.2f}"})
                                 .background_gradient(axis=0, cmap=cmap),use_container_width=True, height=900,
                                 hide_index=True)

                # -------------------- CURRENT SEASON DATA
                st.title(f"{selected_player_home} Season {CURRENT_YEAR}")
                current_player_home_file_path = f"{home_team_url}/{selected_player_home_url}.csv"

                try:
                    file_content = private_repo.get_contents(current_player_home_file_path)
                    content_decoded = base64.b64decode(file_content.content)
                    csv_data = BytesIO(content_decoded)
                    current_player_home_2024_df = pd.read_csv(csv_data)
                    # Your processing steps
                    current_player_home_2024_df['Date'] = pd.to_datetime(current_player_home_2024_df['Date'],
                                                                         dayfirst=True)
                    current_player_home_2024_df = current_player_home_2024_df.drop(columns=drop_columns_2024)
                    current_player_home_2024_df['DisplayRound'] = current_player_home_2024_df['Round'].apply(
                        lambda x: finals_round_mapping.get(x, x))
                    columns_to_display = [col for col in current_player_home_2024_df.columns if
                                          col not in exclude_columns]
                    current_player_home_2024_df = current_player_home_2024_df.sort_values(by="Date")
                except Exception as e:
                    current_player_home_2024_df = pd.DataFrame(columns=dummy_columns)

                # The height calculation would need to be adjusted for an empty DataFrame scenario
                height = (len(current_player_home_2024_df) + 1) * 35 + 3 if not current_player_home_2024_df.empty else 0

                # Custom axis configuration
                custom_axis = alt.Axis(
                    title="Round",
                    titleFontSize=25,
                    labelFontSize=17,
                    labelAngle=0,
                )

                # Create the line chart with sorted 'DisplayRound'
                line_chart = alt.Chart(current_player_home_2024_df).mark_line(
                    color="#488f31",
                    strokeWidth=3
                ).encode(
                    x=alt.X('DisplayRound:N', axis=custom_axis, sort=round_names),  # Apply sort here
                    y=alt.Y("D", axis=alt.Axis(title="Disposals 🟢", labelAngle=0, titleFontSize=40, labelFontSize=17))
                )

                # Create the point chart with sorted 'DisplayRound'
                point_chart = alt.Chart(current_player_home_2024_df).mark_point(
                    size=300,
                    color="#488f31",
                    strokeWidth=4,
                    filled=True
                ).encode(
                    x=alt.X('DisplayRound:N', axis=custom_axis, sort=round_names),  # Apply sort here
                    y=alt.Y("D", axis=alt.Axis(title="Disposals 🟢", labelAngle=0, titleFontSize=40)),
                    tooltip=[
                        alt.Tooltip(field="Round", title="Round"),
                        alt.Tooltip(field="D", title="Disposals"),
                    ]
                )

                # Goals Line Chart
                goals_line_chart = alt.Chart(current_player_home_2024_df).mark_line(
                    color="#488f31",  # Specified green color for goals
                    strokeWidth=3
                ).encode(
                    x=alt.X('DisplayRound:N', axis=custom_axis, sort=round_names),
                    y=alt.Y("G",
                            axis=alt.Axis(title="Goals 🟢 Behinds 🔴", labelAngle=0, titleFontSize=30, labelFontSize=17,
                                          format='d')))

                # Goals Point Chart
                goals_point_chart = alt.Chart(current_player_home_2024_df).mark_point(
                    size=300,
                    color="#488f31",  # Matching green color for goals points
                    strokeWidth=3,
                    filled=True
                ).encode(
                    x=alt.X('DisplayRound:N', sort=round_names),
                    y=alt.Y("G", scale=alt.Scale(nice=False)),
                    tooltip=[
                        alt.Tooltip("Round", title="Round"),
                        alt.Tooltip("G", title="Goals"),
                    ]
                )

                # Behinds Point Chart
                behinds_point_chart = alt.Chart(current_player_home_2024_df).mark_point(
                    size=100,
                    color="#f54242",  # Specified red color for behinds
                    filled=True
                ).encode(
                    x=alt.X('DisplayRound:N', sort=round_names),
                    y=alt.Y("B",
                            axis=alt.Axis(title="Goals 🟢 Behinds 🔴", labelAngle=0, titleFontSize=30, labelFontSize=17,
                                          format='d')),
                    tooltip=[
                        alt.Tooltip("Round", title="Round"),
                        alt.Tooltip("B", title="Behinds"),
                    ]
                )

                # Create a rule mark for the average goals
                average_disposals_rule = alt.Chart(
                    pd.DataFrame({f'{chosen_type} Disposals': [current_player_home_chosen_average_disposals]})).mark_rule(
                    color="#AEC6CF",
                    strokeWidth=2.5,
                    strokeDash=[5, 5]
                ).encode(
                    y=f'{chosen_type} Disposals:Q'
                )


                # Create a rule mark for the average goals
                average_goals_rule = alt.Chart(pd.DataFrame({f'{chosen_type} Goals': [current_player_home_chosen_average_goals]})).mark_rule(
                    color="#AEC6CF",
                    strokeWidth=2.5,
                    strokeDash=[5, 5]
                ).encode(
                    y=f'{chosen_type} Goals:Q'
                )


                # Combine disposal points, lines, average line
                disposal_chart = alt.layer(line_chart, point_chart, average_disposals_rule)
                # Combine goal points, behind points, lines, average line
                combined_goals_behinds_chart = alt.layer(goals_line_chart, goals_point_chart, behinds_point_chart, average_goals_rule)

                col1, col2 = st.columns(2)

                # Place each chart in a column
                with col1:
                    st.altair_chart(disposal_chart, use_container_width=True, theme="streamlit")
                with col2:
                    st.altair_chart(combined_goals_behinds_chart, use_container_width=True, theme="streamlit")

                if not current_player_home_2024_df.empty:
                    # Display Dataframe of Current Chosen Player Stats current year data
                    st.dataframe(current_player_home_2024_df[columns_to_display].style.format(
                        {'Date': lambda x: x.strftime('%d-%m-%Y')}).background_gradient(axis=0, cmap=cmap,
                        subset=[col for col in current_player_home_2024_df.columns if col not in exclude_columns_cmap]),
                        hide_index=True, use_container_width=True, height=height)
                else:
                    st.write(f"No {CURRENT_YEAR} Game Data to display for {selected_player_home}")




                # ------------------- PREVIOUS GAMES
                st.title(f"{selected_player_home} Previous games vs. {away_team}")

                for csv_name2, df in csv_dict_H2H.items():
                    if home_team in csv_name2:
                        # Logic for home team DataFrame
                        df["Year"] = df["Year"].astype(str)
                        current_player_home_prev_vs_opponent_df = df[df["Player Name"] == selected_player_home]
                        current_player_home_prev_vs_opponent_average_disposals = current_player_home_prev_vs_opponent_df["D"].mean()
                        current_player_home_prev_vs_opponent_average_goals = current_player_home_prev_vs_opponent_df["G"].mean()

                        # Rearrange columns for clarity
                        columns_except_year = [col for col in current_player_home_prev_vs_opponent_df.columns if col != 'Year']
                        columns_except_year.insert(1, 'Year')
                        current_player_home_prev_vs_opponent_df = current_player_home_prev_vs_opponent_df[columns_except_year]

                        columns_to_display_h2h = [col for col in current_player_home_prev_vs_opponent_df.columns if
                                                  col not in exclude_columns]

                        # Display the select player previous games dataframe
                        if not current_player_home_prev_vs_opponent_df.empty:
                            st.dataframe(current_player_home_prev_vs_opponent_df[columns_to_display_h2h].style.format({'Date': lambda x: x.strftime('%d-%m-%Y')})
                                         .background_gradient(axis=0, cmap=cmap), use_container_width=True,
                                         hide_index=True)
                        else:
                            st.write(f"No Previous Game Data to display for {selected_player_home}")

                        custom_axis = alt.Axis(
                            title='Year',
                            titleFontSize=25,
                            tickCount=5,
                            labelExpr="year(datum.value)",
                            labelFontSize=20
                        )

                        # Disposal Chart using Date for x-axis
                        disposal_chart = alt.Chart(current_player_home_prev_vs_opponent_df).mark_point(
                            size=300,
                            color="#488f31",
                            strokeWidth=4,
                            filled=True
                        ).encode(
                            x=alt.X('Date:T', axis=custom_axis,
                                    scale=alt.Scale(domainMin=2021, domainMax=2025, nice=True)),
                            # Use 'Date' for x-axis but label it as 'Year' for clarity
                            y=alt.Y("D", axis=alt.Axis(title="Disposals 🟢", labelAngle=0, titleFontSize=40)),
                            tooltip=[
                                alt.Tooltip(field="Year", title="Year"),
                                alt.Tooltip(field="Round", title="Round"),
                                alt.Tooltip(field="D", title="Disposals"),
                            ]
                        )

                        # Disposal Line Chart
                        disposal_line_chart = alt.Chart(current_player_home_prev_vs_opponent_df).mark_line(
                            color="#488f31",  # Adjust color to match your disposal points
                            strokeWidth=3  # Adjust strokeWidth to match your styling
                        ).encode(
                            x=alt.X('Date:T', axis=custom_axis),
                            y=alt.Y("D", axis=alt.Axis(title="Disposals 🟢", labelAngle=0, titleFontSize=40))
                        )


                        # Goals Chart using Date for x-axis
                        goals_chart = alt.Chart(current_player_home_prev_vs_opponent_df).mark_point(
                            size=300,
                            color="#488f31",
                            strokeWidth=4,
                            filled=True
                        ).encode(
                            x=alt.X('Date:T', axis=custom_axis, scale=alt.Scale(domainMin=2021, domainMax=2025,
                                                                                nice=True)),
                            # Use 'Date' for x-axis but label it as 'Year'
                            y=alt.Y("G",
                                    axis=alt.Axis(title="Goals 🟢 Behinds 🔴", labelAngle=0, format='d', tickCount=5, titleFontSize=30),
                                    scale=alt.Scale(domainMin=0, nice=False)),
                            tooltip=[
                                alt.Tooltip(field="Year", title="Year"),
                                alt.Tooltip(field="Round", title="Round"),
                                alt.Tooltip(field="G", title="Goals")
                            ]
                        )

                        # Goals Line Chart
                        goals_line_chart = alt.Chart(current_player_home_prev_vs_opponent_df).mark_line(
                            color="#488f31",  # You can choose a different color for distinction
                            strokeWidth=3  # Match the point border thickness
                        ).encode(
                            x=alt.X('Date:T', axis=custom_axis,
                                    scale=alt.Scale(domainMin=2021, domainMax=2025, nice=True)),
                            y=alt.Y("G", axis=alt.Axis(labelAngle=0, format='d', tickCount=5,
                                                       titleFontSize=30))
                        )

                        # Behinds Chart using Date for x-axis
                        behinds_chart = alt.Chart(current_player_home_prev_vs_opponent_df).mark_circle(size=100, color="#f54242").encode(
                            x=alt.X('Date:T', axis=custom_axis,
                                    scale=alt.Scale(domainMin=2021, domainMax=2025, nice=False)),
                            # Same custom axis for behinds
                            y=alt.Y("B", axis=alt.Axis(title="Goals 🟢 Behinds 🔴", format='d', tickCount=5, titleFontSize=30),
                                    scale=alt.Scale(domainMin=0, nice=False)),
                            tooltip=[
                                alt.Tooltip(field="Year", title="Year"),
                                alt.Tooltip(field="Round", title="Round"),
                                alt.Tooltip(field="B", title="Behinds")
                            ]
                        )

                        # Create a rule mark for the average goals
                        average_disposals_rule = alt.Chart(
                            pd.DataFrame({f'Average Disposals vs {away_team}': [
                                current_player_home_prev_vs_opponent_average_disposals]})).mark_rule(
                            color="#AEC6CF",
                            strokeWidth=2.5,
                            strokeDash=[5, 5]
                        ).encode(
                            y=f'Average Disposals vs {away_team}:Q'
                        )

                        # Create a rule mark for the average goals
                        average_goals_rule = alt.Chart(pd.DataFrame(
                            {f'Average Goals vs {away_team}': [current_player_home_prev_vs_opponent_average_goals]})).mark_rule(
                            color="#AEC6CF",
                            strokeWidth=2.5,
                            strokeDash=[5, 5]
                        ).encode(
                            y=f'Average Goals vs {away_team}:Q'
                        )

                        # Combine disposal points, lines, average line
                        combined_disposal_chart = alt.layer(disposal_line_chart, disposal_chart, average_disposals_rule)

                        # Combine goal points, behinds points, goal lines, average line
                        combined_chart = alt.layer(goals_chart, behinds_chart, goals_line_chart, average_goals_rule)

                        # Make labels and titles bigger
                        combined_disposal_chart = combined_disposal_chart.configure_axisY(labelFontSize=20, titleFontSize=20)
                        combined_chart = combined_chart.configure_axisY(labelFontSize=30, titleFontSize=20)

                        st.write("")

                        # Using st.columns to create two columns
                        col1, col2 = st.columns(2)

                        # Place each chart in a column
                        with col1:
                            st.altair_chart(combined_disposal_chart, use_container_width=True, theme="streamlit")

                        with col2:
                            st.altair_chart(combined_chart, use_container_width=True, theme="streamlit")


        with away_team_tab:
            if away_team in csv_name:
                # Load Headers and H2H Data
                parsed_H2H_Team_data_string = parse_team_H2H_data(away_team, previous_H2H_csv, False)
                st.subheader(f"Previous H2H vs {home_team}: {parsed_H2H_Team_data_string}")
                st.subheader(csv_name)
                # Load Away Team DF
                df = csv_df.sort_values(by=['Disposals'], ascending=False)

                # Create columns for layout
                col1, col2 = st.columns([1, 6])

                # Sort player names alphabetically and create st.radio in the first column for player select
                with col1:
                    sorted_players_away = sorted(df['Player'].unique())
                    selected_player_away = st.radio("Select a Player", sorted_players_away)
                    selected_player_away_url = players_df.loc[players_df['Player'] == selected_player_away, 'name_url'].iloc[0]

                current_player_away_chosen_average_df = df[df["Player"] == selected_player_away]
                current_player_away_chosen_average_disposals = current_player_away_chosen_average_df["Disposals"].iloc[0]
                current_player_away_chosen_average_goals = current_player_away_chosen_average_df["Goals"].iloc[0]

                # Display the DataFrame in the second column
                with col2:
                    st.dataframe(df[styled_columns].style.format({"Disposals": "{:.2f}", "Goals": "{:.2f}",
                                                                  "Behinds": "{:.2f}", "Frees For": "{:.2f}"})
                                 .background_gradient(axis=0, cmap=cmap), use_container_width=True, height=900,
                                 hide_index=True)

                # -------------------- CURRENT SEASON DATA
                st.title(f"{selected_player_away} Season {CURRENT_YEAR}")
                current_player_away_file_path = f"{away_team_url}/{selected_player_away_url}.csv"

                try:
                    file_content = private_repo.get_contents(current_player_away_file_path)
                    content_decoded = base64.b64decode(file_content.content)
                    csv_data = BytesIO(content_decoded)
                    current_player_away_2024_df = pd.read_csv(csv_data)
                    current_player_away_2024_df['Date'] = pd.to_datetime(current_player_away_2024_df['Date'],
                                                                         dayfirst=True)
                    current_player_away_2024_df = current_player_away_2024_df.drop(columns=drop_columns_2024)
                    current_player_away_2024_df['DisplayRound'] = current_player_away_2024_df['Round'].apply(
                        lambda x: finals_round_mapping.get(x, x))
                    columns_to_display = [col for col in current_player_away_2024_df.columns if
                                          col not in exclude_columns]
                    current_player_away_2024_df = current_player_away_2024_df.sort_values(by="Date")

                except Exception as e:
                    current_player_away_2024_df = pd.DataFrame(columns=dummy_columns)

                # Adjust the height calculation for an empty DataFrame scenario
                height = (len(current_player_away_2024_df) + 1) * 35 + 3 if not current_player_away_2024_df.empty else 0

                # Custom axis configuration
                custom_axis = alt.Axis(
                    title="Round",
                    titleFontSize=25,
                    labelFontSize=17,
                    labelAngle=0,
                )

                # Create the line chart with sorted 'DisplayRound'
                line_chart = alt.Chart(current_player_away_2024_df).mark_line(
                    color="#488f31",
                    strokeWidth=3
                ).encode(
                    x=alt.X('DisplayRound:N', axis=custom_axis, sort=round_names),  # Apply sort here
                    y=alt.Y("D", axis=alt.Axis(title="Disposals 🟢", labelAngle=0, titleFontSize=40, labelFontSize=17))
                )

                # Create the point chart with sorted 'DisplayRound'
                point_chart = alt.Chart(current_player_away_2024_df).mark_point(
                    size=300,
                    color="#488f31",
                    strokeWidth=4,
                    filled=True
                ).encode(
                    x=alt.X('DisplayRound:N', axis=custom_axis, sort=round_names),  # Apply sort here
                    y=alt.Y("D", axis=alt.Axis(title="Disposals 🟢", labelAngle=0, titleFontSize=40)),
                    tooltip=[
                        alt.Tooltip(field="Round", title="Round"),
                        alt.Tooltip(field="D", title="Disposals"),
                    ]
                )

                # Goals Line Chart
                goals_line_chart = alt.Chart(current_player_away_2024_df).mark_line(
                    color="#488f31",  # Specified green color for goals
                    strokeWidth=3
                ).encode(
                    x=alt.X('DisplayRound:N', axis=custom_axis, sort=round_names),
                    y=alt.Y("G",
                            axis=alt.Axis(title="Goals 🟢 Behinds 🔴", labelAngle=0, titleFontSize=30, labelFontSize=17,
                                          format='d')))

                # Goals Point Chart
                goals_point_chart = alt.Chart(current_player_away_2024_df).mark_point(
                    size=300,
                    color="#488f31",  # Matching green color for goals points
                    strokeWidth=3,
                    filled=True
                ).encode(
                    x=alt.X('DisplayRound:N', sort=round_names),
                    y=alt.Y("G", scale=alt.Scale(nice=False)),
                    tooltip=[
                        alt.Tooltip("Round", title="Round"),
                        alt.Tooltip("G", title="Goals"),
                    ]
                )

                # Behinds Point Chart
                behinds_point_chart = alt.Chart(current_player_away_2024_df).mark_point(
                    size=100,
                    color="#f54242",  # Specified red color for behinds
                    filled=True
                ).encode(
                    x=alt.X('DisplayRound:N', sort=round_names),
                    y=alt.Y("B",
                            axis=alt.Axis(title="Goals 🟢 Behinds 🔴", labelAngle=0, titleFontSize=30, labelFontSize=17,
                                          format='d')),
                    tooltip=[
                        alt.Tooltip("Round", title="Round"),
                        alt.Tooltip("B", title="Behinds"),
                    ]
                )

                # Create a rule mark for the average goals
                average_disposals_rule = alt.Chart(
                    pd.DataFrame(
                        {f'{chosen_type} Disposals': [current_player_away_chosen_average_disposals]})).mark_rule(
                    color="#AEC6CF",
                    strokeWidth=2.5,
                    strokeDash=[5, 5]
                ).encode(
                    y=f'{chosen_type} Disposals:Q'
                )

                # Create a rule mark for the average goals
                average_goals_rule = alt.Chart(
                    pd.DataFrame({f'{chosen_type} Goals': [current_player_away_chosen_average_goals]})).mark_rule(
                    color="#AEC6CF",
                    strokeWidth=2.5,
                    strokeDash=[5, 5]
                ).encode(
                    y=f'{chosen_type} Goals:Q'
                )

                # Combine disposal points, lines, average line
                disposal_chart = alt.layer(line_chart, point_chart, average_disposals_rule)
                # Combine goal points, behind points, lines, average line
                combined_goals_behinds_chart = alt.layer(goals_line_chart, goals_point_chart, behinds_point_chart,
                                                         average_goals_rule)

                col1, col2 = st.columns(2)

                # Place each chart in a column
                with col1:
                    st.altair_chart(disposal_chart, use_container_width=True, theme="streamlit")
                with col2:
                    st.altair_chart(combined_goals_behinds_chart, use_container_width=True, theme="streamlit")


                if not current_player_away_2024_df.empty:
                    # Display Dataframe of Current Chosen Player Stats current year data
                    st.dataframe(current_player_away_2024_df[columns_to_display].style.format(
                        {'Date': lambda x: x.strftime('%d-%m-%Y')})
                                 .background_gradient(axis=0, cmap=cmap,
                                                      subset=[
                                                          col for col in current_player_away_2024_df.columns if
                                                          col not in exclude_columns_cmap]),
                                 hide_index=True, use_container_width=True, height=height)
                else:
                    st.write(f"No {CURRENT_YEAR} Game Data to display for {selected_player_away}")

                # Display Dataframe of Current Chosen Player Stats current year data


                # ------------------- PREVIOUS GAMES
                st.title(f"{selected_player_away} Previous games vs. {home_team}")

                for csv_name2, df in csv_dict_H2H.items():
                    if away_team in csv_name2:
                        # Logic for away team DataFrame
                        df["Year"] = df["Year"].astype(str)
                        current_player_away_prev_vs_opponent_df = df[df["Player Name"] == selected_player_away]

                        # Rearrange columns for clarity
                        columns_except_year = [col for col in current_player_away_prev_vs_opponent_df.columns if
                                               col != 'Year']
                        columns_except_year.insert(1, 'Year')
                        current_player_away_prev_vs_opponent_df = current_player_away_prev_vs_opponent_df[
                            columns_except_year]

                        columns_to_display_h2h = [col for col in current_player_away_prev_vs_opponent_df.columns if
                                                  col not in exclude_columns]

                        current_player_away_prev_vs_opponent_average_disposals = current_player_away_prev_vs_opponent_df["D"].mean()
                        current_player_away_prev_vs_opponent_average_goals = current_player_away_prev_vs_opponent_df["G"].mean()

                        # Display the select player previous games dataframe
                        if not current_player_away_prev_vs_opponent_df.empty:
                            st.dataframe(current_player_away_prev_vs_opponent_df[columns_to_display_h2h].style.format(
                                {'Date': lambda x: x.strftime('%d-%m-%Y')})
                                         .background_gradient(axis=0, cmap=cmap), use_container_width=True,
                                         hide_index=True)
                        else:
                            st.write(f"No Previous Game Data to display for {selected_player_home}")

                        custom_axis = alt.Axis(
                            title='Year',
                            titleFontSize=25,
                            tickCount=5,
                            labelExpr="year(datum.value)",
                            labelFontSize=20
                        )

                        # Disposal Chart using Date for x-axis
                        disposal_chart = alt.Chart(current_player_away_prev_vs_opponent_df).mark_point(
                            size=300,
                            color="#488f31",
                            strokeWidth=4,
                            filled=True
                        ).encode(
                            x=alt.X('Date:T', axis=custom_axis,
                                    scale=alt.Scale(domainMin=2021, domainMax=2025, nice=True)),
                            # Use 'Date' for x-axis but label it as 'Year' for clarity
                            y=alt.Y("D", axis=alt.Axis(title="Disposals 🟢", labelAngle=0, titleFontSize=40)),
                            tooltip=[
                                alt.Tooltip(field="Year", title="Year"),
                                alt.Tooltip(field="Round", title="Round"),
                                alt.Tooltip(field="D", title="Disposals"),
                            ]
                        )

                        # Disposal Line Chart
                        disposal_line_chart = alt.Chart(current_player_away_prev_vs_opponent_df).mark_line(
                            color="#488f31",  # Adjust color to match your disposal points
                            strokeWidth=3  # Adjust strokeWidth to match your styling
                        ).encode(
                            x=alt.X('Date:T', axis=custom_axis),
                            y=alt.Y("D", axis=alt.Axis(title="Disposals 🟢", labelAngle=0, titleFontSize=40))
                        )

                        # Goals Chart using Date for x-axis
                        goals_chart = alt.Chart(current_player_away_prev_vs_opponent_df).mark_point(
                            size=300,
                            color="#488f31",
                            strokeWidth=4,
                            filled=True
                        ).encode(
                            x=alt.X('Date:T', axis=custom_axis, scale=alt.Scale(domainMin=2021, domainMax=2025,
                                                                                nice=True)),
                            # Use 'Date' for x-axis but label it as 'Year'
                            y=alt.Y("G",
                                    axis=alt.Axis(title="Goals 🟢 Behinds 🔴", labelAngle=0, format='d', tickCount=5,
                                                  titleFontSize=30),
                                    scale=alt.Scale(domainMin=0, nice=False)),
                            tooltip=[
                                alt.Tooltip(field="Year", title="Year"),
                                alt.Tooltip(field="Round", title="Round"),
                                alt.Tooltip(field="G", title="Goals")
                            ]
                        )

                        # Goals Line Chart
                        goals_line_chart = alt.Chart(current_player_away_prev_vs_opponent_df).mark_line(
                            color="#488f31",  # You can choose a different color for distinction
                            strokeWidth=3  # Match the point border thickness
                        ).encode(
                            x=alt.X('Date:T', axis=custom_axis,
                                    scale=alt.Scale(domainMin=2021, domainMax=2025, nice=True)),
                            y=alt.Y("G", axis=alt.Axis(labelAngle=0, format='d', tickCount=5,
                                                       titleFontSize=30))
                        )

                        # Behinds Chart using Date for x-axis
                        behinds_chart = alt.Chart(current_player_away_prev_vs_opponent_df).mark_circle(size=100,
                                                                                                       color="#f54242").encode(
                            x=alt.X('Date:T', axis=custom_axis,
                                    scale=alt.Scale(domainMin=2021, domainMax=2025, nice=False)),
                            # Same custom axis for behinds
                            y=alt.Y("B", axis=alt.Axis(title="Goals 🟢 Behinds 🔴", format='d', tickCount=5,
                                                       titleFontSize=30),
                                    scale=alt.Scale(domainMin=0, nice=False)),
                            tooltip=[
                                alt.Tooltip(field="Year", title="Year"),
                                alt.Tooltip(field="Round", title="Round"),
                                alt.Tooltip(field="B", title="Behinds")
                            ]
                        )

                        # Create a rule mark for the average goals
                        average_disposals_rule = alt.Chart(
                            pd.DataFrame({f'Average Disposals vs {home_team}': [
                                current_player_away_prev_vs_opponent_average_disposals]})).mark_rule(
                            color="#AEC6CF",
                            strokeWidth=2.5,
                            strokeDash=[5, 5]
                        ).encode(
                            y=f'Average Disposals vs {home_team}:Q'
                        )

                        # Create a rule mark for the average goals
                        average_goals_rule = alt.Chart(pd.DataFrame(
                            {f'Average Goals vs {home_team}': [current_player_away_prev_vs_opponent_average_goals]})).mark_rule(
                            color="#AEC6CF",
                            strokeWidth=2.5,
                            strokeDash=[5, 5]
                        ).encode(
                            y=f'Average Goals vs {home_team}:Q'
                        )

                        # Combine disposal points, lines, average line
                        combined_disposal_chart = alt.layer(disposal_line_chart, disposal_chart, average_disposals_rule)

                        # Combine goal points, behinds points, goal lines, average line
                        combined_chart = alt.layer(goals_chart, behinds_chart, goals_line_chart, average_goals_rule)

                        # Make labels and titles bigger
                        combined_disposal_chart = combined_disposal_chart.configure_axisY(labelFontSize=20,
                                                                                          titleFontSize=20)
                        combined_chart = combined_chart.configure_axisY(labelFontSize=30, titleFontSize=20)

                        st.write("")

                        # Using st.columns to create two columns
                        col1, col2 = st.columns(2)

                        # Place each chart in a column
                        with col1:
                            st.altair_chart(combined_disposal_chart, use_container_width=True, theme="streamlit")

                        with col2:
                            st.altair_chart(combined_chart, use_container_width=True, theme="streamlit")