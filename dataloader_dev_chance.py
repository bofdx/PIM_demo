import sqlite3
import streamlit as st
import pandas as pd
import uuid
import os

st.write("For uploading metadata into the database using the Excel template")


upload_files = st.file_uploader(
    "Upload your files (CSV or Excel):",
    type=["csv", "xlsx", "xlsm"],
    accept_multiple_files=True
)

if upload_files:
    for file in upload_files:
        file_ext = os.path.splitext(file.name)[-1].lower()
        if file_ext == ".csv":
            df_load = pd.read_csv(file, header =2)
        elif file_ext in (".xlsx", ".xlsm"):
            df_load = pd.read_excel(file,sheet_name= "Template", header =2)
        else:
            st.error(f"Unsupported file type: {file_ext}")
            continue

   
        # Display name and file size
        st.write(f"**File Name:** {file.name}")
        st.write(f"**File Size:** {file.size / 1024:.2f} KB")

        # Show 5 rows of our df
        st.write("Preview the head of the dataframe")
        st.dataframe(df_load.head())

        if 'period' not in df_load.columns:
            period_value = st.text_input("Enter a value for 'period':")

        if period_value:
            df_load['period'] = period_value
            st.success(f"'period' column created with value: {period_value}")
        else:
            st.warning("Please enter a value for 'period' to proceed.")

        # Add a UUID column
        df_load["dev_chance_id"] = [str(uuid.uuid4()) for _ in range(len(df_load))]

        # Ensure column order matches the SQLite metadata table
        expected_cols = ['dev_chance_id', 'period', 'project','associated_rmus','net_2c_mmboe','p_tech','p_fin','p_time','p_econ','p_mark','p_inf','p_ext','commitment','odp_phase','comment','hub']

        df_load = df_load[expected_cols]

        st.dataframe(df_load.head())
        
        # # Define the probability columns
        # probability_cols = ['p_tech', 'p_fin', 'p_time', 'p_econ', 'p_mark', 'p_inf', 'p_ext']
        # # Row-wise minimum of probability columns
        # df_load['min_chance'] = df_load[probability_cols].min(axis=1)      
        # # Row-wise average of probability columns
        # df_load['pd_ave'] = df_load[probability_cols].mean(axis=1) * df_load['commitment']
        
# Gold button using HTML and unsafe_allow_html
st.markdown("""
    <style>
    .gold-button > button {
        background-color: gold !important;
        color: black !important;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Display the button
#if st.container().markdown('<div class="gold-button">', unsafe_allow_html=True):
    if st.button("Commit to Database"):
        # Create database
        connection = sqlite3.connect("PIM3.db")
        cursor = connection.cursor()

        # SQLite pragmas
        cursor.execute("PRAGMA foreign_keys = ON") # Enforce FK constraints

        # SQL insert
        insert_sql_2 = f"""
        INSERT INTO dev_chance ({', '.join(expected_cols)})
        VALUES ({', '.join(['?' for _ in expected_cols])})
        """
        cursor.executemany(insert_sql_2, df_load.values.tolist())

        connection.commit()
        connection.close()

        st.success("Data committed to PIM.db successfully ✅")
        
if st.button("View Data"):
    connection = sqlite3.connect("PIM3.db")
    cursor = connection.cursor()
    datapreview = pd.read_sql_query("SELECT * FROM dev_chance", connection)
    connection.close()  # Good practice

    st.dataframe(datapreview)  # Use Streamlit to display the DataFrame



