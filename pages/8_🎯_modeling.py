import streamlit as st
import pandas as pd
import os
import json
from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata
from datetime import datetime
from utils.file_naming import generate_filename

UPLOAD_DIR = "uploads"

st.title("CTGAN Model Training")

st.markdown("""
### CTGAN Model Configuration

Configure and train a CTGAN (Conditional Tabular GAN) model:
1. Select your data and metadata files
2. Configure CTGAN parameters
3. Train the model
4. Save the trained model
""")

# Get available files
if os.path.exists(UPLOAD_DIR):
    csv_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.csv')]
    json_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.json')]
    
    if not csv_files or not json_files:
        st.warning("Please ensure you have both CSV data files and metadata JSON files in your uploads.")
    else:
        # File selection
        col1, col2 = st.columns(2)
        
        with col1:
            selected_data = st.selectbox(
                "Select Data File:",
                csv_files
            )
        
        with col2:
            selected_metadata = st.selectbox(
                "Select Metadata File:",
                json_files
            )
        
        if selected_data and selected_metadata:
            try:
                with st.spinner("Loading data and metadata..."):
                    # Load data
                    data_path = os.path.join(UPLOAD_DIR, selected_data)
                    data = pd.read_csv(data_path)
                    
                    # Create new metadata instance
                    metadata = SingleTableMetadata()
                    
                    # First detect from dataframe
                    metadata.detect_from_dataframe(data)
                    
                    # Load saved metadata properties
                    metadata_path = os.path.join(UPLOAD_DIR, selected_metadata)
                    with open(metadata_path, 'r') as f:
                        saved_metadata = json.load(f)
                    
                    # Get table info
                    table_name = list(saved_metadata['tables'].keys())[0]
                    table_metadata = saved_metadata['tables'][table_name]
                    
                    # Update column properties
                    for column_name, column_props in table_metadata['columns'].items():
                        if column_name in metadata.columns:
                            update_args = {'sdtype': column_props['sdtype']}
                            
                            # Add other properties if they exist
                            if 'computer_representation' in column_props:
                                update_args['computer_representation'] = column_props['computer_representation']
                            if 'datetime_format' in column_props:
                                update_args['datetime_format'] = column_props['datetime_format']
                            
                            metadata.update_column(column_name, **update_args)
                    
                    # Explicitly set primary key to None
                    metadata.set_primary_key(None)
                    
                    st.success("Metadata loaded successfully!")
                    
                    # CTGAN parameters
                    st.markdown("### CTGAN Parameters")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        epochs = st.number_input("Training Epochs", min_value=1, value=300)
                        batch_size = st.number_input("Batch Size", min_value=1, value=500)
                        log_frequency = st.checkbox("Log Frequency", value=True)
                        
                    with col2:
                        generator_dim = st.text_input("Generator Dimensions", "128, 128, 128")
                        discriminator_dim = st.text_input("Discriminator Dimensions", "128, 128, 128")
                        embedding_dim = st.number_input("Embedding Dimension", min_value=1, value=128)
                    
                    # Convert string dimensions to tuples
                    generator_dim = tuple(map(int, generator_dim.split(',')))
                    discriminator_dim = tuple(map(int, discriminator_dim.split(',')))
                    
                    # Initialize CTGAN with metadata
                    model = CTGANSynthesizer(
                        metadata,
                        epochs=epochs,
                        batch_size=batch_size,
                        log_frequency=log_frequency,
                        generator_dim=generator_dim,
                        discriminator_dim=discriminator_dim,
                        embedding_dim=embedding_dim
                    )

                    # Model filename handling
                    if 'model_filename' not in st.session_state:
                        st.session_state.model_filename = generate_filename(
                            "model_ctgan",
                            source_files=[selected_data, selected_metadata]
                        )

                    # Update default filename when files change
                    current_default = generate_filename(
                        "model_ctgan",
                        source_files=[selected_data, selected_metadata]
                    )
                    if current_default != st.session_state.model_filename:
                        st.session_state.model_filename = current_default

                    # Filename input
                    custom_filename = st.text_input(
                        "Model filename",
                        value=st.session_state.model_filename,
                        help="You can modify the filename (without extension)",
                        key="model_filename_input"
                    ).strip()

                    # Train and Save buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Train Model"):
                            with st.spinner(f"Training CTGAN model for {epochs} epochs..."):
                                model.fit(data)
                                st.session_state.trained_model = model
                                st.success("Model training completed!")
                    
                    with col2:
                        if st.button("Save Model") and 'trained_model' in st.session_state:
                            try:
                                if not custom_filename:
                                    st.error("Filename cannot be empty")
                                    st.stop()
                                
                                # Ensure .pkl extension
                                if not custom_filename.endswith('.pkl'):
                                    model_filename = f"{custom_filename}.pkl"
                                else:
                                    model_filename = custom_filename
                                
                                model_path = os.path.join(UPLOAD_DIR, model_filename)
                                st.session_state.trained_model.save(model_path)
                                
                                st.success(f"""
                                Model saved successfully as: {model_filename}
                                Training details:
                                - Epochs: {epochs}
                                - Batch size: {batch_size}
                                - Data file: {selected_data}
                                - Metadata file: {selected_metadata}
                                """)
                            except Exception as e:
                                st.error(f"Error saving model: {str(e)}")
                
            except Exception as e:
                st.error(f"Error during model training: {str(e)}")
                st.error("Please check if your metadata file is compatible with the data.")
else:
    st.warning("Upload directory does not exist. Please check your configuration.") 