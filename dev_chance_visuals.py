import sqlite3
import streamlit as st
import pandas as pd
import numpy as np

connection = sqlite3.connect("PIM3.db")
full_df = pd.read_sql_query("SELECT * FROM dev_chance", connection)
connection.close()

full_df['Pd'] = full_df[ 'p_tech', 'p_fin', 'p_time', 'p_econ', 'p_mark', 'p_inf', 'p_ext'].mean(axis = 1)*full_df['commitment']

if st.button("View All Data in dev_chance"):
    try:
        st.subheader("📊 All Data in dev_chance Table")
        st.dataframe(full_df)
    except Exception as e:
        st.error(f"Error reading from DB: {e}")

st.subheader("Probability of Technical Success")
st.bar_chart(full_df,x="project", y ="p_tech", color = "odp_phase", height = 600, x_label = "Project", y_label = "Probability of Technical Succes", use_container_width=True)

