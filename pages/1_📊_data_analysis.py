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
            # Initialize filename in session state if not exists
            file_key = f"custom_filename_{uploaded_file.name}"
            if file_key not in st.session_state:
                default_name = os.path.splitext(uploaded_file.name)[0]
                st.session_state[file_key] = default_name

            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Custom filename input
                custom_filename = st.text_input(
                    f"Filename for {uploaded_file.name}",
                    value=st.session_state[file_key],
                    help="You can modify the filename (without extension)",
                    key=f"input_{file_key}"
                ).strip()
                
                # Update session state
                st.session_state[file_key] = custom_filename

            with col2:
                if st.button(f"Save {uploaded_file.name}", key=f"save_{uploaded_file.name}"):
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
                        df = pd.read_csv(uploaded_file)
                        df.to_csv(save_path, index=False)
                        
                        st.success(f"""
                        File saved successfully as: {save_filename}
                        
                        You can view and manage your files in the 'Uploaded Files' page.
                        """)
                    except Exception as e:
                        st.error(f"Error saving file: {str(e)}")
except Exception as e:
    st.error(f"Upload error: {str(e)}")