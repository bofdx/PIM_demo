import streamlit as st
import pandas as pd
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
            df_load = pd.read_csv(file, header =1)
        elif file_ext in (".xlsx", ".xlsm"):
            df_load = pd.read_excel(file,sheet_name= "Template", header =1)
        else:
            st.error(f"Unsupported file type: {file_ext}")
            continue

    
        # Display name and file size
        st.write(f"**File Name:** {file.name}")
        st.write(f"**File Size:** {file.size / 1024:.2f} KB")

        # Show 5 rows of our df
        st.write("Preview the head of the dataframe")
        st.dataframe(df_load.head())

        # Add a UUID column
        df_load["dev_chance_id"] = [str(uuid.uuid4()) for _ in range(len(df_data_load_2))]

        # Ensure column order matches the SQLite metadata table
        expected_cols = ['dev_chance_id', 'period', 'project','associated_rmus','net_2c_mmboe','p_tech','p_fin','p_time','p_econ','p_mark','p_inf','p_ext','commitment','odp_phase','comment','hub']

        df_load = df_load[expected_cols]

        st.dataframe(df_load.head())
        
        
        # Options for data cleaning
        st.subheader("Data Cleaning Options")
        if st.checkbox(f"Clean Data for {file.name}"):
            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"Remove Duplicates from {file.name}"):
                    df_load.drop_duplicates(inplace=True)
                    st.write("Duplicates removed!")

            with col2:
                if st.button(f"Fill Missing Values for {file.name}"):
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    df_load[numeric_cols] = df_load[numeric_cols].fillna(99999999)
                    st.write("Missing numeric values filled with 99999999")

