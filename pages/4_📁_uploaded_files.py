import streamlit as st
import os
import pandas as pd
from datetime import datetime

# Use the same upload directory as defined in the data analysis page
UPLOAD_DIR = "uploads"

st.title("Uploaded Files")

st.markdown("""
### List of Uploaded Files

View, download, or remove uploaded files:
""")

def delete_file(file_path):
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        st.error(f"Error deleting file: {str(e)}")
        return False

def get_file_type(filename):
    extension = filename.split('.')[-1].lower()
    type_mapping = {
        'csv': 'Data File',
        'json': 'Metadata File',
        'pkl': 'Model File'
    }
    return type_mapping.get(extension, 'Unknown')

def get_file_details(file_path):
    file_size = os.path.getsize(file_path)
    creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
    filename = os.path.basename(file_path)
    
    file_details = {
        "Filename": filename,
        "Type": get_file_type(filename),
        "Size (KB)": f"{file_size/1024:.2f}",
        "Upload Date": creation_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Add row and column counts only for CSV/Excel files
    if file_path.endswith(('.csv', '.xlsx')):
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            file_details["Rows"] = len(df)
            file_details["Columns"] = len(df.columns)
        except Exception as e:
            st.warning(f"Could not read file contents for {filename}")
            file_details["Rows"] = "N/A"
            file_details["Columns"] = "N/A"
    else:
        file_details["Rows"] = "N/A"
        file_details["Columns"] = "N/A"
    
    return file_details

if os.path.exists(UPLOAD_DIR):
    files = os.listdir(UPLOAD_DIR)
    
    if not files:
        st.info("No files have been uploaded yet.")
    else:
        # Create a list to store file details
        file_details = []
        
        for file in files:
            file_path = os.path.join(UPLOAD_DIR, file)
            try:
                details = get_file_details(file_path)
                file_details.append(details)
            except Exception as e:
                st.error(f"Error processing file {file}: {str(e)}")
        
        # Create a DataFrame from file details and display it
        if file_details:
            df_files = pd.DataFrame(file_details)
            st.dataframe(df_files, use_container_width=True)
            
            # File management section
            st.markdown("### File Management")
            
            # Create columns for download and delete buttons
            for file in files:
                col1, col2 = st.columns([3, 1])
                file_path = os.path.join(UPLOAD_DIR, file)
                
                with col1:
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"Download {file}",
                            data=f,
                            file_name=file,
                            mime="application/octet-stream"
                        )
                
                with col2:
                    if st.button(f"🗑️ Delete {file}"):
                        if delete_file(file_path):
                            st.success(f"Successfully deleted {file}")
                            st.experimental_rerun()
            
            # Add a button to delete all files
            st.markdown("---")
            if st.button("🗑️ Delete All Files", type="secondary"):
                if st.warning("Are you sure you want to delete all files?"):
                    for file in files:
                        file_path = os.path.join(UPLOAD_DIR, file)
                        delete_file(file_path)
                    st.success("All files deleted successfully!")
                    st.experimental_rerun()
else:
    st.warning("Upload directory does not exist. Please upload files first.") 