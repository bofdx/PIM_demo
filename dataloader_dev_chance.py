with tab:
    try:
        file_ext = os.path.splitext(file.name)[-1].lower()
        df_key = f"df_{file.name}"
        original_df_key = f"original_df_{file.name}"

        # Load only once into session_state
        if df_key not in st.session_state:
            if file_ext == ".csv":
                df = pd.read_csv(file, header=2)
            elif file_ext in (".xlsx", ".xlsm"):
                df = pd.read_excel(file, sheet_name="Template", header=2)
            else:
                st.error(f"Unsupported file type: {file_ext}")
                continue

            # Handle missing 'period'
            if 'period' not in df.columns:
                period_key = f"period_{file.name}"
                period_value = st.text_input("Enter a value for 'period':", key=period_key)
                if period_value:
                    df['period'] = period_value
                    st.success(f"'period' column added with value: {period_value}")
                else:
                    st.warning("Please enter a value for 'period' to continue.")
                    continue

            # Add UUIDs
            df["dev_chance_id"] = [str(uuid.uuid4()) for _ in range(len(df))]

            # Reorder columns
            df = df[[col for col in expected_cols if col in df.columns]]

            # Save original and editable
            st.session_state[original_df_key] = df.copy()
            st.session_state[df_key] = df.copy()

        # Load editable version
        df = st.session_state[df_key]

        # Reset changes
        if st.button("🔄 Reset Changes", key=f"reset_{file.name}"):
            st.session_state[df_key] = st.session_state[original_df_key].copy()
            df = st.session_state[df_key]
            st.success("Changes have been reset to original upload.")

        # Track Changes toggle
        if st.checkbox("📌 Show Differences from Original", key=f"diff_toggle_{file.name}"):
            original_df = st.session_state[original_df_key]

            def highlight_changes(val, orig):
                return 'background-color: #ffd6d6' if pd.notna(val) and val != orig else ''

            comparison = df.copy()
            for col in df.columns:
                if col in original_df.columns:
                    comparison[col] = df[col].combine(original_df[col], lambda new, old: new)
                    comparison[col] = comparison.apply(
                        lambda row: row[col], axis=1
                    )
            styled = df.style.apply(
                lambda x: [
                    'background-color: #ffd6d6' if (
                        pd.notna(x[col]) and x[col] != st.session_state[original_df_key][col].iloc[x.name]
                    ) else '' for col in df.columns
                ],
                axis=1
            )
            st.dataframe(styled)

        # Live editor
        st.markdown("### ✍️ Data Editor")
        df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={"dev_chance_id": st.column_config.Column(disabled=True)},
            key=f"editor_{file.name}"
        )
        st.session_state[df_key] = df

        # Commit button
        if st.button(f"✅ Commit '{file.name}' to Database", key=f"commit_{file.name}"):
            try:
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
