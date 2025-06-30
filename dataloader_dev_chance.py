import sqlite3
import streamlit as st
import pandas as pd
import uuid
import os

st.title("Metadata Loader for PIM3")
st.write("Upload your Excel or CSV files using the provided template format.")

# State holders
if "dataframes" not in st.session_state:
    st.session_state["dataframes"] = {}

upload_files = st.file_uploader(
    "Upload your files (CSV or Excel):",
    type=["csv", "xlsx", "xlsm"],
    accept_multiple_files=True
)

# Expected structure
expected_cols = ['dev_chance_id', 'period', 'project', 'associated_rmus', 'net_2c_mmboe',
                 'p_tech', 'p_fin', 'p_time', 'p_econ', 'p_mark', 'p_inf', 'p_ext',
                 'commitment', 'odp_phase', 'comment', 'hub']

if upload_files:
    for file in upload_files:
        file_ext = os.path.splitext(file.name)[-1].lower()

        try:
            if file_ext == ".csv":
                df_load = pd.read_csv(file, header=2)
            elif file_ext in (".xlsx", ".xlsm"):
                df_load = pd.read_excel(file, sheet_name="Template", header=2)
            else:
                st.error(f"Unsupported file type: {file_ext}")
                continue

            st.write(f"**File Name:** {file.name}")
            st.write(f"**File Size:** {file.size / 1024:.2f} KB")
            st.dataframe(df_load.head())

            # Ask for 'period' only if it's missing
            if 'period' not in df_load.columns:
                period_key = f"period_input_{file.name}"
                period_value = st.text_input(f"Enter a value for 'period' in {file.name}:", key=period_key)

                if period_value:
                    df_load['period'] = period_value
                    st.success(f"'period' column created with value: {period_value}")
                else:
                    st.warning(f"Waiting for 'period' input for {file.name}. Skipping this file.")
                    continue  # Don't proceed with this file until period is entered

            # Add UUIDs
            df_load["dev_chance_id"] = [str(uuid.uuid4()) for _ in range(len(df_load))]

            # Ensure column alignment
            df_load = df_load[[col for col in expected_cols if col in df_load.columns]]

            # Store in session state for commit later
            st.session_state["dataframes"][file.name] = df_load

            #st.write(f"Final Preview for {file.name}:")
           # st.dataframe(df_load.head())

        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")

# Show combined preview
if st.session_state["dataframes"]:
    combined_df = pd.concat(st.session_state["dataframes"].values(), ignore_index=True)
    st.subheader("📋 Combined Final Preview of All Uploaded Files")
    st.dataframe(combined_df.head(20))


# Commit to DB
if st.button("Commit to Database"):
    if not st.session_state["dataframes"]:
        st.warning("No data to commit. Please upload and complete all required fields.")
    else:
        try:
            connection = sqlite3.connect("PIM3.db")
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")

            for name, df in st.session_state["dataframes"].items():
                insert_sql = f"""
                INSERT INTO dev_chance ({', '.join(df.columns)})
                VALUES ({', '.join(['?' for _ in df.columns])})
                """
                cursor.executemany(insert_sql, df.values.tolist())

            connection.commit()
            st.success("Data committed to PIM3.db successfully ✅")

        except sqlite3.IntegrityError as e:
            st.error(f"Database IntegrityError: {e}")
        except sqlite3.Error as e:
            st.error(f"Database Error: {e}")
        except Exception as e:
            st.error(f"Unexpected Error: {e}")
        finally:
            connection.close()

# View committed data
if st.button("View Data"):
    try:
        connection = sqlite3.connect("PIM3.db")
        datapreview = pd.read_sql_query("SELECT * FROM dev_chance", connection)
        connection.close()
        st.dataframe(datapreview)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
