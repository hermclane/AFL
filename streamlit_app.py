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
CURRENT_ROUND = 1
CURRENT_YEAR = 2024

# HIDE ACCESS KEY
load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
g = Github(st.secrets.clientid.clientid, st.secrets.clientsecret.clientsecret)
# g = Github(GITHUB_TOKEN)

GITHUB_TOKEN2 = os.getenv('GITHUB_TOKEN2')
