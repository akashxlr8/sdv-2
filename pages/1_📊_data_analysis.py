import streamlit as st
import pandas as pd
import os
from datetime import datetime
import shutil

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

st.title("Data Analysis")

st.markdown("""
### Data Analysis Page

Upload your data and analyze it here:
""")

try:
    # File uploader
    uploaded_files = st.file_uploader(
        "Upload CSV files",
        type=['csv'],
        accept_multiple_files=True
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.markdown(f"### File: {uploaded_file.name}")
            
            # Initialize filename in session state if not exists
            file_key = f"custom_filename_{uploaded_file.name}"
            if file_key not in st.session_state:
                default_name = os.path.splitext(uploaded_file.name)[0]
                st.session_state[file_key] = default_name

            # Load and display data preview
            df = pd.read_csv(uploaded_file)
            
            # Custom filename input
            custom_filename = st.text_input(
                "Save as:",
                value=st.session_state[file_key],
                help="You can modify the filename (without extension)",
                key=f"input_{file_key}"
            )
            custom_filename = custom_filename.strip() if custom_filename else ""
            
            # Update session state
            st.session_state[file_key] = custom_filename
            
            # Save button
            if st.button(f"Save", key=f"save_{uploaded_file.name}"):
                try:
                    if not custom_filename:
                        st.error("Filename cannot be empty")
                        st.stop()
                    
                    # Ensure .csv extension
                    if not custom_filename.endswith('.csv'):
                        save_filename = f"{custom_filename}.csv"
                    else:
                        save_filename = custom_filename
                    
                    # Save the file
                    save_path = os.path.join(UPLOAD_DIR, save_filename)
                    df.to_csv(save_path, index=False)
                    
                    st.success(f"""
                    File saved successfully as: {save_filename}
                    
                    You can view and manage your files in the 'File Manager' page.
                    """)
                except Exception as e:
                    st.error(f"Save error: {str(e)}")
            
            # Create three columns for better layout
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                # Display file info
                st.info(f"""
                **File Details:**
                - Rows: {len(df)}
                - Columns: {len(df.columns)}
                - Size: {uploaded_file.size / 1024:.2f} KB
                """)
            
            with col2:
                # Display column info
                st.markdown("#### Column Types")
                col_types = pd.DataFrame({
                    'Type': df.dtypes
                }).reset_index()
                col_types.columns = ['Column', 'Type']
                st.dataframe(col_types, use_container_width=True)
            
            # Show data preview in full width
            st.markdown("#### Data Preview")
            st.dataframe(
                df.head(),
                use_container_width=True
            )

except Exception as e:
    st.error(f"Upload error: {str(e)}")