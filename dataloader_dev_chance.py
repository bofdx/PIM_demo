import sqlite3
import streamlit as st
import pandas as pd
import uuid
import os

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

st.write("Please check each data extract individually before committing it to the database.")

# UI for per-file workflow
if upload_files:
    tab_titles = [file.name for file in upload_files]
    tabs = st.tabs(tab_titles)

    for file, tab in zip(upload_files, tabs):
        with tab:
            try:
                file_ext = os.path.splitext(file.name)[-1].lower()
                df_key = f"df_{file.name}"
                original_df_key = f"original_df_{file.name}"

                # Load and process only if not already in session_state
                if df_key not in st.session_state:
                    if file_ext == ".csv":
                        df = pd.read_csv(file, header=2)
                    elif file_ext in (".xlsx", ".xlsm"):
                        df = pd.read_excel(file, sheet_name="Template", header=2)
                    else:
                        st.error(f"Unsupported file type: {file_ext}")
                        continue

                    # If 'period' missing, ask user to input
                    if 'period' not in df.columns:
                        period_key = f"period_{file.name}"
                        period_value = st.text_input("Enter a value for 'period':", key=period_key)
                        if period_value:
                            df['period'] = period_value
                            st.success(f"'period' column added with value: {period_value}")
                        else:
                            st.warning("Please enter a value for 'period' to continue.")
                            continue  # skip this tab if no period entered

                    # Add UUIDs
                    df["dev_chance_id"] = [str(uuid.uuid4()) for _ in range(len(df))]

                    # Reorder columns
                    df = df[[col for col in expected_cols if col in df.columns]]

                    # Store both original and editable copies
                    st.session_state[original_df_key] = df.copy()
                    st.session_state[df_key] = df.copy()
               
                # Pull from session_state
                df = st.session_state[df_key]


                # Track version for editor reset
                editor_key = f"editor_{file.name}"
                if f"{editor_key}_version" not in st.session_state:
                    st.session_state[f"{editor_key}_version"] = 0

                st.markdown("### Data Editor")
              
                # Reset button
                if st.button("🔄 Reset Changes", key=f"reset_{file.name}"):
                    st.session_state[df_key] = st.session_state[original_df_key].copy()
                    df = st.session_state[df_key]
                    st.session_state[f"{editor_key}_version"] += 1  # Trigger editor refresh
                    st.success("Changes have been reset to original upload.")
                
                # Data editor UI with dynamic key to force re-render
               
                df = st.data_editor(
                    df,
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={"dev_chance_id": st.column_config.Column(disabled=True)},
                    key=f"{editor_key}_{st.session_state[f'{editor_key}_version']}"
                )
                
                # Save edited df back to session
                st.session_state[df_key] = df

                # Commit button
                if st.button(f"Commit '{file.name}' to Database", key=f"commit_{file.name}"):
                    try:
                        # Validation: Check for blanks except 'comment'
                        cols_to_check = [col for col in df.columns if col != 'comment']
                        if df[cols_to_check].isnull().any().any():
                            st.error("❌ Cannot commit. One or more required fields are blank (excluding 'comment').")
                        else:
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
                        if 'connection' in locals():
                            connection.close()

            except Exception as e:
                st.error(f"Unhandled error processing {file.name}: {e}")
