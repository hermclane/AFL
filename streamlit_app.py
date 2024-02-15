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

# CHANGE ROUND EVERY WEEK
CURRENT_ROUND = 12

# HIDE ACCESS KEY
load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
g = Github(st.secrets.clientid.clientid, st.secrets.clientsecret.clientsecret)

st.set_page_config(page_title="Unseen Stats",
                   page_icon="🔮",
                   layout='wide')

@st.cache_resource
def open_repo():
    # specify the repository URL
    repo = g.get_repo('hermclane/AFL')
    return repo


repo = open_repo()


@st.cache_data
def read_fixture():
    # load fixture data once
    fixture_df = pd.read_excel(r"https://raw.githubusercontent.com/hermclane/AFL/main/AFLFixtures2023.xlsx")
    return fixture_df

# Make Dataframes
fixture_df = read_fixture()
current_round_fixture_df = fixture_df[fixture_df["Round Number"] == CURRENT_ROUND]
# Get the list of match strings from the "Match String" column of the current_round_fixture_df DataFrame
match_list = current_round_fixture_df["Match String"].tolist()

parent_folder_path = f"Round_{CURRENT_ROUND}"


@st.cache_data
def get_parent_folder_contents():
    # load parent folder contents once
    parent_folder_contents = repo.get_contents(parent_folder_path)
    return parent_folder_contents


parent_folder_contents = get_parent_folder_contents()

folder_list = [content.name for content in parent_folder_contents if content.type == 'dir']

sorted_folder_list = [folder_name for match_str in match_list for folder_name in folder_list if match_str in folder_name]


@st.cache_data
def get_image():
    image_url = 'https://raw.githubusercontent.com/hermclane/AFL/main/Logo.png'
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    return image


# set image
image = get_image()
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

# Create Date and time for header display
game_datetime_np = current_round_fixture_df.loc[current_round_fixture_df['Match String'] == selected_folder_name, 'Date'].values[0]
game_datetime_str = game_datetime_np.astype(str)
game_datetime_obj = datetime.strptime(game_datetime_str[:-3], '%Y-%m-%dT%H:%M:%S.%f')
game_day_time_str = game_datetime_obj.strftime('%A, %I:%M %p')

# Get venue for header display
location = current_round_fixture_df.loc[current_round_fixture_df['Match String'] == selected_folder_name, 'Location'].values[0]

# Configure Game Header
header_display = f'{selected_folder_name} - {location} - {game_day_time_str} AEST'

# Define the colors for the colormap
colors = [(0, 0, 0, 0), "#488f31"]  # Replace "#488f31" with your desired dark pastel green color

# Create the colormap
cmap = plt.colors.LinearSegmentedColormap.from_list("custom_cmap", colors)


@st.cache_data
def load_csv_data(_repo, selected_folder_path):
    csv_dict = {}
    for file in repo.get_contents(selected_folder_path):
        if file.name.endswith('.csv'):
            df = pd.read_csv(io.StringIO(file.decoded_content.decode('utf-8')))
            csv_dict[file.name.replace('.csv', '')] = df
    return csv_dict


# Load CSV data into a dictionary
csv_dict = load_csv_data(repo, selected_folder_path)

# Display DFs
st.header(header_display)
chosen_type = st.selectbox("Game Averages", ("Season Average", "Last 10 Average", "Last 5 Average", "Last 3 Average"))
home_team_tab, away_team_tab = st.tabs([f'Home: {home_team}', f'Away: {away_team}'])

# Display each CSV file as a table
for csv_name, csv_df in csv_dict.items():
    if chosen_type in csv_name:
        with home_team_tab:
            if home_team in csv_name:
                st.subheader(csv_name)
                df = csv_df.sort_values(by=['Disposals'], ascending=False)
                st.dataframe(df.style.format({"Disposals": "{:.2f}", "Goals": "{:.2f}", "Behinds": "{:.2f}", 
                                              "Frees For":  "{:.2f}"}).background_gradient(axis=0, cmap=cmap), 
                             height=1000, use_container_width=True)
        with away_team_tab:
            if away_team in csv_name:
                st.subheader(csv_name)
                df = csv_df.sort_values(by=['Disposals'], ascending=False)
                st.dataframe(df.style.format({"Disposals": "{:.2f}", "Goals": "{:.2f}", "Behinds": "{:.2f}", 
                                              "Frees For":  "{:.2f}"}).background_gradient(axis=0, cmap=cmap), 
                             height=1000, use_container_width=True)



