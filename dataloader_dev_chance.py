import sqlite3
import streamlit as st
import pandas as pd
import uuid
import os

st.title("Metadata Loader for PIM3")
st.write("Upload your Excel or CSV files using the provided template format.")

# Expected columns
expected_cols = ['dev_chance_id', 'period', 'project', 'associated_rmus', 'net_2c_mmboe',
                 'p_tech', 'p_fin', 'p_time', 'p_econ', 'p_mark', 'p_inf', 'p_ext',
                 'commitment', 'odp_phase', 'comment', 'hub']

# File upload
upload_files = st.file_uploader(
    "Upload your files (CSV or Excel):",
    type=["csv", "xlsx", "xlsm"],
    accept_multiple_files=True
)

# UI for per-file workflow
if upload_files:
    tab_titles = [file.name for file in upload_files]
    tabs = st.tabs(tab_titles)

    for file, tab in zip(upload_files, tabs):
        with tab:
            try:
                file_ext = os.path.splitext(file.name)[-1].lower()

                if file_ext == ".csv":
                    df = pd.read_csv(file, header=2)
                elif file_ext in (".xlsx", ".xlsm"):
                    df = pd.read_excel(file, sheet_name="Template", header=2)
                else:
                    st.error(f"Unsupported file type: {file_ext}")
                    continue

                st.subheader(f"📄 File: {file.name}")
                st.write(f"**Size:** {file.size / 1024:.2f} KB")
                st.dataframe(df.head())

                # If 'period' missing, ask user to input
                if 'period' not in df.columns:
                    period_key = f"period_{file.name}"
                    period_value = st.text_input("Enter a value for 'period':", key=period_key)
                    if period_value:
                        df['period'] = period_value
                        st.success(f"'period' column added with value: {period_value}")
                    else:
                        st.warning("Please enter a value for 'period' to continue.")
                        st.stop()

                # Add UUIDs
                df["dev_chance_id"] = [str(uuid.uuid4()) for _ in range(len(df))]

                # Reorder columns
                df = df[[col for col in expected_cols if col in df.columns]]

                st.markdown("### Final Preview Before Commit")
                st.dataframe(df.head(20))

                # Commit button inside this tab
                if st.button(f"Commit '{file.name}' to Database", key=f"commit_{file.name}"):
                    try:
                        connection = sqlite3.connect("PIM3.db")
                        cursor = connection.cursor()
                        cursor.execute("PRAGMA foreign_keys = ON")

                        insert_sql = f"""
                        INSERT INTO dev_chance ({', '.join(df.columns)})
                        VALUES ({', '.join(['?' for _ in df.columns])})
                        """
                        cursor.executemany(insert_sql, df.values.tolist())
                        connection.commit()
                        st.success(f"✅ '{file.name}' committed to PIM3.db successfully")

                    except sqlite3.IntegrityError as e:
                        st.error(f"❌ IntegrityError: {e}")
                    except sqlite3.Error as e:
                        st.error(f"❌ SQLite Error: {e}")
                    except Exception as e:
                        st.error(f"❌ Unexpected Error: {e}")
                    finally:
                        connection.close()

            except Exception as e:
                st.error(f"Unhandled error processing {file.name}: {e}")

# View full table
if st.button("View All Data in dev_chance"):
    try:
        connection = sqlite3.connect("PIM3.db")
        full_df = pd.read_sql_query("SELECT * FROM dev_chance", connection)
        connection.close()
        st.subheader("📊 All Data in dev_chance Table")
        st.dataframe(full_df)
    except Exception as e:
        st.error(f"Error reading from DB: {e}")
