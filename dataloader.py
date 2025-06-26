import streamlit as st
import pandas as pd
import os

st.title("Metadata Loader")
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
            df = pd.read_csv(file)
        elif file_ext in (".xlsx", ".xlsm"):
            df = pd.read_excel(file)
        else:
            st.error(f"Unsupported file type: {file_ext}")
            continue

        # Display name and file size
        st.write(f"**File Name:** {file.name}")
        st.write(f"**File Size:** {file.size / 1024:.2f} KB")

        # Show 5 rows of our df
        st.write("Preview the head of the dataframe")
        st.dataframe(df.head())

        # Options for data cleaning
        st.subheader("Data Cleaning Options")
        if st.checkbox(f"Clean Data for {file.name}"):
            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"Remove Duplicates from {file.name}"):
                    df.drop_duplicates(inplace=True)
                    st.write("Duplicates removed!")

            with col2:
                if st.button(f"Fill Missing Values for {file.name}"):
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    df[numeric_cols] = df[numeric_cols].fillna(99999999)
                    st.write("Missing numeric values filled with 99999999")

        # Choose Specific Columns to Keep or Convert
        st.subheader("Select Columns to Convert")
        columns = st.multiselect(f"Choose Columns for {file.name}", df.columns, default=list(df.columns))
        df = df[columns]

        # Create some simple visuals
        st.subheader("Data Visuals")
        if st.checkbox(f"Show Visual for {file.name}"):
            numeric_df = df.select_dtypes(include='number')
            if numeric_df.shape[1] >= 3:
                st.bar_chart(numeric_df.iloc[:, 1:3])
            else:
                st.warning("Not enough numeric columns to display columns 2 and 3.")
