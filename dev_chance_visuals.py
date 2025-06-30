import sqlite3
import streamlit as st
import pandas as pd
import numpy as np

connection = sqlite3.connect("PIM3.db")
full_df = pd.read_sql_query("SELECT * FROM dev_chance", connection)
connection.close()

cols = ['p_tech', 'p_fin', 'p_time', 'p_econ', 'p_mark', 'p_inf', 'p_ext']
full_df['pd'] = full_df[cols].mean(axis=1) * full_df['commitment']
full_df['p_min'] = full_df[cols].min(axis=1)

if st.button("View All Data in dev_chance"):
    try:
        st.subheader("📊 All Data in dev_chance Table")
        st.dataframe(full_df)
    except Exception as e:
        st.error(f"Error reading from DB: {e}")

if full_df.empty:
    st.write("No Data To Display")
else:
    st.subheader("Probability of Development")
    st.bar_chart(full_df,x="project", y ="pd", color = "odp_phase", height = 600, x_label = "Project", y_label = "Probability Development ", use_container_width=True)

