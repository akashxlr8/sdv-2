import streamlit as st
import pandas as pd
import os
import pickle
from datetime import datetime
from sdv.metadata import SingleTableMetadata
from sdv.single_table import CTGANSynthesizer

UPLOAD_DIR = "uploads"

st.title("Synthetic Data Generation")

st.markdown("""
### Generate Synthetic Data

1. Select your trained model
2. Configure generation parameters
3. Generate synthetic data
""")

if os.path.exists(UPLOAD_DIR):
    # Get available model files
    model_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.pkl')]
    
    if not model_files:
        st.warning("No trained models found. Please train a model first in the Modeling page.")
    else:
        # Model selection
        selected_model = st.selectbox(
            "Select trained model:",
            model_files
        )
        
        if selected_model:
            try:
                # Load the model
                model_path = os.path.join(UPLOAD_DIR, selected_model)
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                
                # Generation parameters
                num_rows = st.number_input(
                    "Number of rows to generate:", 
                    min_value=1, 
                    value=100
                )
                
                # Initialize filename in session state if not exists
                file_key = f"synthetic_filename_{selected_model}"
                if file_key not in st.session_state:
                    default_name = f"synthetic_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    st.session_state[file_key] = default_name
                
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
                
                if st.button("Generate Synthetic Data"):
                    with st.spinner("Generating synthetic data..."):
                        # Generate synthetic data
                        synthetic_data = model.sample(num_rows=num_rows)
                        
                        # Save synthetic data
                        if not custom_filename:
                            st.error("Filename cannot be empty")
                            st.stop()
                        
                        # Ensure .csv extension
                        if not custom_filename.endswith('.csv'):
                            output_filename = f"{custom_filename}.csv"
                        else:
                            output_filename = custom_filename
                        
                        output_path = os.path.join(UPLOAD_DIR, output_filename)
                        synthetic_data.to_csv(output_path, index=False)
                        
                        st.success(f"Generated synthetic data saved as: {output_filename}")
                        
                        # Display preview
                        st.markdown("### Data Preview")
                        st.dataframe(synthetic_data.head())
                        
            except Exception as e:
                st.error(f"Error loading model or generating data: {str(e)}")
else:
    st.warning("Upload directory does not exist. Please check your configuration.")