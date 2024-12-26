import streamlit as st
import os
import pandas as pd
from datetime import datetime

# Use the same upload directory as defined in the data analysis page
UPLOAD_DIR = "uploads"

st.title("File Manager")

st.markdown("""
### File Manager

View, manage, and organize your files:
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

def get_file_source(filename):
    # Check file extension first
    extension = filename.split('.')[-1].lower()
    
    # Metadata files are always generated
    if extension == 'json':
        return 'Generated'
    
    # For other files, check if they contain indicators of being generated
    generated_indicators = ['synthetic', 'model_ctgan', 'generated']
    return 'Generated' if any(indicator in filename.lower() for indicator in generated_indicators) else 'Uploaded'

def get_file_details(file_path):
    file_size = os.path.getsize(file_path)
    creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
    filename = os.path.basename(file_path)
    
    file_details = {
        "Filename": filename,
        "Type": get_file_type(filename),
        "Source": get_file_source(filename),
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

def rename_file(old_path, new_name):
    try:
        directory = os.path.dirname(old_path)
        extension = os.path.splitext(old_path)[1]
        new_path = os.path.join(directory, f"{new_name}{extension}")
        
        # Check if new filename already exists
        if os.path.exists(new_path):
            return False, "A file with this name already exists"
        
        os.rename(old_path, new_path)
        return True, "File renamed successfully"
    except Exception as e:
        return False, f"Error renaming file: {str(e)}"

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
            st.dataframe(
                df_files,
                use_container_width=True,
                column_config={
                    "Filename": st.column_config.TextColumn(
                        "Filename",
                        width="large",
                        help="File name with extension",
                        max_chars=-1  # No limit on characters
                    ),
                    "Type": st.column_config.TextColumn(
                        "Type",
                        width="small"
                    ),
                    "Source": st.column_config.TextColumn(
                        "Source",
                        width="small"
                    ),
                    "Size (KB)": st.column_config.NumberColumn(
                        "Size (KB)",
                        width="small"
                    ),
                    "Upload Date": st.column_config.DatetimeColumn(
                        "Upload Date",
                        width="medium"
                    )
                }
            )
            
            # File management section
            st.markdown("### File Management")
            
            # Create columns for file actions
            for file in files:
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                file_path = os.path.join(UPLOAD_DIR, file)
                base_name = os.path.splitext(file)[0]
                
                with col1:
                    new_name = st.text_input(
                        "New name",
                        value=base_name,
                        key=f"rename_{file}",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    if st.button("✏️ Rename", key=f"rename_btn_{file}"):
                        if new_name != base_name:
                            success, message = rename_file(file_path, new_name)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                
                with col3:
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download",
                            data=f,
                            file_name=file,
                            mime="application/octet-stream",
                            key=f"download_{file}"
                        )
                
                with col4:
                    if st.button("🗑️ Delete", key=f"delete_{file}"):
                        if delete_file(file_path):
                            st.success(f"Successfully deleted {file}")
                            st.rerun()
            
            # Add a button to delete all files
            st.markdown("---")
            if st.button("🗑️ Delete All Files", type="secondary"):
                if st.warning("Are you sure you want to delete all files?"):
                    for file in files:
                        file_path = os.path.join(UPLOAD_DIR, file)
                        delete_file(file_path)
                    st.success("All files deleted successfully!")
                    st.rerun()
else:
    st.warning("Upload directory does not exist. Please upload files first.") 