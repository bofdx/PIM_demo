import streamlit as st
import pandas as pd
import os

from st_pages import add_page_title, get_nav_from_toml

# Set up our app
#st.set_page_config(page_title="Metadata Loader", layout='wide')

st.set_page_config(layout='wide')

sections = st.sidebar.toggle('Sections', value = True, key = 'use_sections')

nav = get_nav_from_toml(".streamlit/pages_sections.toml" if sections else ".streamlit/pages.toml")

pg = st.navigation(nav)

add_page_title(pg)

pg.run()

