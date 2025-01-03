import streamlit as st
import pandas as pd
import os
import json
import re
from sdv.evaluation.single_table import evaluate_quality
from sdv.evaluation.single_table import get_column_plot
from sdv.evaluation.single_table import get_column_pair_plot
from sdv.evaluation.single_table import run_diagnostic
from sdv.metadata import SingleTableMetadata
import plotly.graph_objects as go
from datetime import datetime
import sdmetrics


UPLOAD_DIR = "uploads"

st.title("Synthetic Data Evaluation")

st.markdown("""
### Evaluate Synthetic Data Quality

1. Select original data
2. Select synthetic data
3. Select metadata file
4. View quality metrics
5. Analyze column distributions
""")

if os.path.exists(UPLOAD_DIR):
    csv_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.csv')]
    json_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.json')]
    
    if len(csv_files) < 2:
        st.warning("Please ensure you have both original and synthetic data files.")
    else:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            original_data = st.selectbox(
                "Select Original Data:",
                csv_files,
                key="original"
            )
        
        with col2:
            synthetic_data = st.selectbox(
                "Select Synthetic Data:",
                csv_files,
                key="synthetic"
            )
        
        with col3:
            metadata_file = st.selectbox(
                "Select Metadata File:",
                json_files,
                key="metadata"
            )
        
        if original_data and synthetic_data and metadata_file:
            try:
                # Load data and metadata
                original_df = pd.read_csv(os.path.join(UPLOAD_DIR, original_data))
                synthetic_df = pd.read_csv(os.path.join(UPLOAD_DIR, synthetic_data))
                
                # Load metadata
                metadata_path = os.path.join(UPLOAD_DIR, metadata_file)
                with open(metadata_path, 'r') as f:
                    metadata_dict = json.load(f)
                
                # Create metadata instance
                metadata = SingleTableMetadata()
                metadata.detect_from_dataframe(original_df)
                
                # Update metadata with saved properties
                table_name = list(metadata_dict['tables'].keys())[0]
                table_metadata = metadata_dict['tables'][table_name]
                
                # Update column properties
                for column_name, column_props in table_metadata['columns'].items():
                    if column_name in metadata.columns:
                        if column_props['sdtype'] == 'id':
                            metadata.set_primary_key(column_name)
                        else:
                            update_args = {'sdtype': column_props['sdtype']}
                            if 'computer_representation' in column_props:
                                update_args['computer_representation'] = column_props['computer_representation']
                            metadata.update_column(column_name, **update_args)
                
                # Diagnostic Evaluation
                if st.button("Run Diagnostic"):
                    progress_placeholder = st.empty()
                    with st.spinner("Running diagnostic checks..."):
                        try:
                            # Redirect stdout to capture progress
                            import io
                            import sys
                            from contextlib import redirect_stdout

                            # Capture the output
                            f = io.StringIO()
                            with redirect_stdout(f):
                                diagnostic = run_diagnostic(
                                    real_data=original_df,
                                    synthetic_data=synthetic_df,
                                    metadata=metadata
                                )
                            
                            # Get the captured output
                            output = f.getvalue()
                            
                            # Display the progress in Streamlit
                            progress_placeholder.text(output)
                            
                            # Parse scores with error handling
                            def extract_score(pattern):
                                match = re.search(pattern, output)
                                return float(match.group(1)) if match else 0.0
                            
                            validity_score = extract_score(r'Data Validity Score: (\d+\.?\d*)%')
                            structure_score = extract_score(r'Data Structure Score: (\d+\.?\d*)%')
                            overall_score = extract_score(r'Overall Score \(Average\): (\d+\.?\d*)%')
                            
                            # Display scores
                            st.markdown("### Diagnostic Results")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric(
                                    "Data Validity Score",
                                    f"{validity_score:.1f}%"
                                )
                            with col2:
                                st.metric(
                                    "Data Structure Score",
                                    f"{structure_score:.1f}%"
                                )
                            with col3:
                                st.metric(
                                    "Overall Score",
                                    f"{overall_score:.1f}%"
                                )
                            
                            # Display detailed results if available
                            if hasattr(diagnostic, 'get_details'):
                                st.markdown("### Detailed Diagnostic Results")
                                st.json(diagnostic.__dict__)
                            
                            if overall_score < 100:
                                st.warning("Some issues were found in the synthetic data. Check the detailed results above.")
                            else:
                                st.success("The synthetic data passed all diagnostic checks!")
                                
                        except Exception as e:
                            st.error(f"Error during diagnostic evaluation: {str(e)}")

                # Quality Evaluation
                if st.button("Evaluate Data Quality"):
                    with st.spinner("Calculating quality metrics..."):
                        # Compute quality report
                        quality_report = evaluate_quality(
                            real_data=original_df,
                            synthetic_data=synthetic_df,
                            metadata=metadata
                        )
                        
                        # Display overall quality score
                        st.markdown("### Overall Quality Score")
                        st.info(f"Quality Score: {quality_report.get_score():.2f}")
                        
                        # Display property scores
                        st.markdown("### Property Scores")
                        
                        try:
                            # Get properties and handle different return formats
                            properties = quality_report.get_properties()
                            
                            if isinstance(properties, list):
                                # Handle list format
                                properties_df = pd.DataFrame([{
                                    'Property': getattr(prop, '__name__', str(prop)),
                                    'Score': f"{getattr(prop, 'score', 0.0):.3f}",
                                    'Description': getattr(prop, 'description', 'N/A')
                                } for prop in properties])
                            elif isinstance(properties, dict):
                                # Handle dictionary format
                                properties_df = pd.DataFrame([{
                                    'Property': name,
                                    'Score': f"{score:.3f}",
                                    'Description': 'N/A'
                                } for name, score in properties.items()])
                            else:
                                # Handle string format or other cases
                                st.write("Quality Report Properties:", properties)
                                properties_df = pd.DataFrame({
                                    'Property': [getattr(prop, 'property_name', str(prop)) for prop in properties],
                                    'Score': [f"{getattr(prop, 'score', 0.0):.3f}" for prop in properties],
                                    'Description': [getattr(prop, 'description', 'N/A') for prop in properties]
                                })
                            
                            # Display using native Streamlit table
                            st.table(properties_df)
                            
                        except Exception as e:
                            st.error(f"Error processing quality report: {str(e)}")
                            st.write("Raw Quality Report:", quality_report)
                        
                        # Column Visualization
                        st.markdown("### Column Visualization")
                        
                        # Get column metadata types
                        column_types = {col: metadata.columns[col]['sdtype'] for col in original_df.columns}
                        
                        # Column selection with type info
                        selected_column = st.selectbox(
                            "Select column to visualize:",
                            options=original_df.columns.tolist(),
                            format_func=lambda x: f"{x} ({column_types[x]})"
                        )
                        
                        if selected_column:
                            try:
                                # Create simple column plot using SDMetrics
                                fig = get_column_plot(
                                    real_data=original_df,
                                    synthetic_data=synthetic_df,
                                    column_name=selected_column,
                                    metadata=metadata
                                )
                                
                                # Display the plot using Streamlit
                                st.plotly_chart(fig)
                                
                                # Option for pair plot
                                st.markdown("### Column Pair Visualization")
                                
                                # Create a list of columns excluding the currently selected one
                                remaining_columns = [col for col in original_df.columns if col != selected_column]
                                
                                second_column = st.selectbox(
                                    "Select second column for pair visualization:",
                                    options=remaining_columns,
                                    format_func=lambda x: f"{x} ({column_types[x]})",
                                    key="second_column"
                                )
                                
                                if second_column:
                                    with st.spinner("Generating pair plot..."):
                                        from sdmetrics.visualization import get_column_pair_plot
                                        
                                        pair_fig = get_column_pair_plot(
                                            real_data=original_df,
                                            synthetic_data=synthetic_df,
                                            column_names=[selected_column, second_column]
                                        )
                                        
                                        # Display the pair plot using Streamlit
                                        st.plotly_chart(pair_fig)
                                        
                            except Exception as e:
                                st.error(f"Error creating visualization: {str(e)}")
                
            except Exception as e:
                st.error(f"Error during evaluation: {str(e)}")
                st.error("Please check if the metadata file is compatible with the data.")
else:
    st.warning("Upload directory does not exist. Please check your configuration.") 