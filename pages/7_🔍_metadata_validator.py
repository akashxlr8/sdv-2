import streamlit as st
import pandas as pd
import os
import json
from sdv.metadata import Metadata, SingleTableMetadata
from datetime import datetime

UPLOAD_DIR = "uploads"

st.title("Metadata Validator")

st.markdown("""
### Metadata Validation

Validate your saved metadata files:
1. Select a metadata file
2. Validate its structure
3. View validation results
4. Visualize metadata relationships
""")

# Get all JSON files from the uploads directory
json_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.json')]

if json_files:
    selected_metadata_file = st.selectbox(
        "Select a metadata file to validate:",
        json_files
    )
    
    if selected_metadata_file and st.button("Validate Metadata"):
        try:
            # Load the metadata from JSON
            metadata_path = os.path.join(UPLOAD_DIR, selected_metadata_file)
            
            # Display the metadata content
            with open(metadata_path, 'r') as f:
                metadata_content = json.load(f)
            
            st.markdown("### Metadata Content")
            st.json(metadata_content)
            
            # Load and validate using SDV
            metadata = Metadata.load_from_json(metadata_path)
            validation_result = metadata.validate()
            
            if validation_result is None:  # validate() returns None if successful
                st.success(f"✅ Metadata in '{selected_metadata_file}' is valid!")
                
                # Show metadata details
                st.markdown("### Metadata Structure")
                for table_name, table_info in metadata.tables.items():
                    st.write(f"**Table:** {table_name}")
                    
                    # Show columns
                    st.write("**Columns:**")
                    cols = []
                    for col_name, col_info in table_info.columns.items():
                        cols.append({
                            'Column': col_name,
                            'SDType': col_info['sdtype'],
                            'Additional Properties': ', '.join([
                                f"{k}: {v}" for k, v in col_info.items() 
                                if k != 'sdtype'
                            ])
                        })
                    
                    st.dataframe(
                        pd.DataFrame(cols),
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Show primary key
                    if table_info.primary_key:
                        st.write(f"**Primary Key:** {table_info.primary_key}")
                    
                    # Show relationships
                    if hasattr(metadata, 'relationships') and metadata.relationships:
                        st.markdown("### Relationships")
                        for rel in metadata.relationships:
                            st.write(
                                f"- {rel['parent_table_name']}.{rel['parent_primary_key']} → "
                                f"{rel['child_table_name']}.{rel['child_foreign_key']}"
                            )
                
                # Ensure session state for visualization
                if 'visualize_clicked' not in st.session_state:
                    st.session_state.visualize_clicked = False

                # Visualization option
                if st.button("Visualize Metadata"):
                    st.session_state.visualize_clicked = True

                if st.session_state.visualize_clicked:
                    try:
                        # Create DOT language representation
                        dot_string = """
                        digraph {
                            node [shape=box, style=filled, fillcolor=lightblue]
                        """
                        
                        # Add nodes and edges for each table
                        for table_name, table_info in metadata_content['tables'].items():
                            # Add table node
                            dot_string += f'\n    "{table_name}" [shape=box, fillcolor=lightgreen]\n'
                            
                            # Add column nodes and their connections
                            for col_name, col_info in table_info['columns'].items():
                                node_name = f"{table_name}_{col_name}"
                                dot_string += f'    "{node_name}" [label="{col_name}\\n({col_info["sdtype"]}")]\n'
                                dot_string += f'    "{table_name}" -> "{node_name}"\n'
                        
                        dot_string += "}"
                        
                        # Render using Streamlit's graphviz_chart
                        st.graphviz_chart(dot_string, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"Error visualizing metadata: {str(e)}")
            
        except Exception as e:
            st.error(f"Error validating metadata: {str(e)}")
            st.error("Please check if the metadata file is in the correct format.")
else:
    st.info("No metadata files found. Please create and save metadata first in the Metadata Manager.") 