import os
import streamlit as st
import pandas as pd
from PIL import Image
from datetime import datetime
import matplotlib as plt

current_round = 9
os.chdir(fr'https://raw.githubusercontent.com/hermclane/AFL/main/Round_{current_round}')
fixture2023_df = pd.read_excel(r"https://raw.githubusercontent.com/hermclane/AFL/main/AFLFixtures2023.xlsx")
current_round_fixture_df = fixture2023_df[fixture2023_df["Round Number"] == current_round]

# Get a list of folders in the current directory
folder_list = os.listdir()

# Get the list of match strings from the "Match String" column of the current_round_fixture_df DataFrame
match_list = current_round_fixture_df["Match String"].tolist()

# Use the match list to create a sorted folder list that is ordered based on the "Match String" column
sorted_folder_list = [folder_name for match_str in match_list for folder_name in folder_list if match_str in folder_name]

st.set_page_config(layout='wide')

# Set the title of the sidebar
image = Image.open(r'https://github.com/hermclane/AFL/blob/84e4af274f607afd7efaaa8ac50b510a8ff90d14/wizard.png')
st.sidebar.image(image, use_column_width=True)
st.sidebar.title(f'Current Round: {current_round}')

# Create an empty dictionary to store the folder names and corresponding team string
folder_team_dict = {}

# Create a sidebar with a list of folders to choose from
selected_folder = st.sidebar.radio('Select a game (Home Team vs Away Team):', sorted_folder_list)

# Get a list of CSV files in the folder
csv_list = [file for file in os.listdir(selected_folder) if file.endswith('.csv')]

# Check if the folder name matches the "Folder url" column of the "current_round_fixture_df"
matching_row = current_round_fixture_df[current_round_fixture_df["Match String"] == selected_folder]
home_team = matching_row["Home Team"].iloc[0]
away_team = matching_row["Away Team"].iloc[0]

# Create Date and time for header display
game_datetime_np = current_round_fixture_df.loc[current_round_fixture_df['Match String'] == selected_folder, 'Date'].values[0]
game_datetime_str = game_datetime_np.astype(str)
game_datetime_obj = datetime.strptime(game_datetime_str[:-3], '%Y-%m-%dT%H:%M:%S.%f')
game_day_time_str = game_datetime_obj.strftime('%A, %I:%M %p')

# Get venue for header display
location = current_round_fixture_df.loc[current_round_fixture_df['Match String'] == selected_folder, 'Location'].values[0]

# Configure Game Header
header_display = f'{selected_folder} - {location} - {game_day_time_str} AEST'

# Select a subset of columns to apply the style formatting to
columns_to_style = ["Disposals", "Goals", "Behinds", "Frees For",
           "15 Dis. %", "20 Dis. %", "25 Dis. %", "1 Goal %", "2 Goals %", "3 Goals %"]

# Define the colors for the colormap
colors = [(0, 0, 0, 0), "#488f31"]  # Replace "#488f31" with your desired dark pastel green color

# Create the colormap
cmap = plt.colors.LinearSegmentedColormap.from_list("custom_cmap", colors)

# Display DFs
if os.path.isdir(selected_folder):
    st.header(header_display)
    chosen_type = st.selectbox("Game Averages", ("Season Average", "Last 5 Average", "Last 3 Average"))
    home_team_tab, away_team_tab = st.tabs([f'Home: {home_team}', f'Away: {away_team}'])

    # Display each CSV file as a table
    for csv_file in csv_list:
        # Check if the file contains the specified file type
        if chosen_type in csv_file:
            with home_team_tab:
                if home_team in csv_file:
                    st.subheader(csv_file.replace('.csv', ''))
                    df = pd.read_csv(os.path.join(selected_folder, csv_file))
                    df = df.sort_values(by=['Disposals'], ascending=False)
                    st.dataframe(df.style.background_gradient(axis=0, cmap=cmap), height=1000, use_container_width=True)


            with away_team_tab:
                if away_team in csv_file:
                    st.subheader(csv_file.replace('.csv', ''))
                    df = pd.read_csv(os.path.join(selected_folder, csv_file))
                    df = df.sort_values(by=['Disposals'], ascending=False)
                    st.dataframe(df.style.background_gradient(axis=0, cmap=cmap), height=1000, use_container_width=True)
