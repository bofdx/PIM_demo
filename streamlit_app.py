import streamlit as st
import pandas as pd
import os

from st_pages import add_page_title, get_nav_from_toml

st.set_page_config(layout='wide')

#sections = st.sidebar.toggle('Sections', value = True, key = 'use_sections')

nav = get_nav_from_toml() #"pages_sections.toml" if sections else "pages.toml")

st.logo("STO LOGO.PNG")

pg = st.navigation(nav)

add_page_title(pg)

pg.run()

