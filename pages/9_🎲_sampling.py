import streamlit as st
import pandas as pd
import os
import pickle
from datetime import datetime
from utils.file_naming import generate_filename

UPLOAD_DIR = "uploads"

st.title("Synthetic Data Sampling")

st.markdown("""
### Generate Synthetic Data Samples

1. Select a trained model
2. Configure sampling parameters
3. Generate and save synthetic data
""")

# Get available model files
if os.path.exists(UPLOAD_DIR):
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
                
                # Sampling configuration
                st.markdown("### Sampling Configuration")
                
                col1, col2 = st.columns(2)
                with col1:
                    num_rows = st.number_input(
                        "Number of rows to generate:", 
                        min_value=1, 
                        value=100
                    )
                
                with col2:
                    batch_size = st.number_input(
                        "Batch size for generation:", 
                        min_value=1, 
                        value=min(1000, num_rows),
                        help="Larger batch sizes are faster but use more memory"
                    )
                
                if st.button("Generate Synthetic Data"):
                    try:
                        with st.spinner(f"Generating {num_rows} synthetic rows..."):
                            # Sample data with only supported parameters
                            synthetic_data = model.sample(
                                num_rows=num_rows,
                                batch_size=batch_size
                            )
                            
                            # Save synthetic data
                            base_filename = generate_filename(
                                "synthetic",
                                source_files=[selected_model]
                            )
                            output_filename = f"{base_filename}.csv"
                            output_path = os.path.join(UPLOAD_DIR, output_filename)
                            synthetic_data.to_csv(output_path, index=False)
                            
                            st.success(f"Generated synthetic data saved as: {output_filename}")
                            
                            # Display results
                            tab1, tab2 = st.tabs(["Preview", "Statistics"])
                            
                            with tab1:
                                st.markdown("### Generated Data Preview")
                                st.dataframe(synthetic_data.head(10))
                            
                            with tab2:
                                st.markdown("### Basic Statistics")
                                st.dataframe(synthetic_data.describe())
                            
                            # Download button
                            st.download_button(
                                label="Download Synthetic Data",
                                data=synthetic_data.to_csv(index=False),
                                file_name=output_filename,
                                mime='text/csv'
                            )
                    
                    except Exception as e:
                        st.error(f"Error generating synthetic data: {str(e)}")
                        st.error("Please check if the model is compatible with the current version of SDV.")
            
            except Exception as e:
                st.error(f"Error loading model: {str(e)}")
else:
    st.warning("Upload directory does not exist. Please check your configuration.") 