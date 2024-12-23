import streamlit as st
import pandas as pd
import os
from datetime import datetime
from backend.logic import (
    create_scalar_range_constraints,
    setup_metadata,
    create_synthesizer,
    save_metadata,
    data_validator
)
from utils.file_naming import generate_filename

UPLOAD_DIR = "uploads"

st.title("Synthetic Data Generation")

st.markdown("""
### Generate Synthetic Data

Select files from your uploads to generate synthetic data:
""")

if os.path.exists(UPLOAD_DIR):
    files = os.listdir(UPLOAD_DIR)
    
    if not files:
        st.info("No files available. Please upload files in the Data Analysis page first.")
    else:
        # Filter only CSV files
        csv_files = [f for f in files if f.endswith('.csv')]
        
        if not csv_files:
            st.warning("No CSV files found. Please upload CSV files for synthetic data generation.")
        else:
            # File selection
            selected_files = st.multiselect(
                "Select CSV files for synthetic data generation:",
                csv_files
            )
            
            if selected_files:
                # Display selected file details
                st.markdown("### Selected Files:")
                for file in selected_files:
                    file_path = os.path.join(UPLOAD_DIR, file)
                    df = pd.read_csv(file_path)
                    st.info(f"""
                    **{file}**
                    - Rows: {len(df)}
                    - Columns: {len(df.columns)}
                    """)
                
                # Process button
                if st.button("Generate Synthetic Data"):
                    try:
                        # Create data dictionary
                        data = {}
                        for file in selected_files:
                            file_path = os.path.join(UPLOAD_DIR, file)
                            table_name = os.path.splitext(file)[0].upper()
                            data[table_name] = pd.read_csv(file_path)
                        
                        # Validate data
                        violations = data_validator(data)
                        if violations:
                            st.warning("Data validation warnings:")
                            for violation in violations:
                                st.write(f"- {violation}")
                        
                        with st.spinner("Setting up metadata..."):
                            # Setup metadata
                            metadata = setup_metadata(data)
                            
                            # Create constraints
                            constraints = create_scalar_range_constraints()
                            
                            # Create synthesizer
                            synthesizer = create_synthesizer(metadata, constraints)
                            
                            # Fit the synthesizer
                            synthesizer.fit(data)
                            
                            st.success("Metadata and synthesizer setup complete!")
                        
                        # After metadata setup
                        if metadata:
                            # Save metadata with proper filename
                            base_filename = generate_filename(
                                "metadata",
                                source_files=selected_files
                            )
                            metadata_filename = f"{base_filename}.json"
                            metadata_path = os.path.join(UPLOAD_DIR, metadata_filename)
                            
                            # Save metadata using the save_metadata function
                            save_metadata(metadata, metadata_path)
                            st.success(f"Metadata saved as: {metadata_filename}")
                        
                        # Generate synthetic data
                        num_rows = st.number_input("Number of rows to generate:", min_value=1, value=100)
                        
                        if st.button("Generate"):
                            with st.spinner("Generating synthetic data..."):
                                synthetic_data = synthesizer.sample(num_rows=num_rows)
                                
                                # Save synthetic data
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                for table_name, df in synthetic_data.items():
                                    output_filename = f"synthetic_{table_name.lower()}_{timestamp}.csv"
                                    output_path = os.path.join(UPLOAD_DIR, output_filename)
                                    df.to_csv(output_path, index=False)
                                    
                                    st.success(f"Generated synthetic data saved as: {output_filename}")
                                    st.dataframe(df.head())
                                st.rerun()
                    
                    except Exception as e:
                        st.error(f"Error generating synthetic data: {str(e)}")
else:
    st.warning("Upload directory does not exist. Please upload files first.") 