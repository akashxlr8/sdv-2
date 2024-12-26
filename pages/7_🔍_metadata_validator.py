import streamlit as st
import pandas as pd
import os
import json
from sdv.metadata import Metadata, SingleTableMetadata
from datetime import datetime

UPLOAD_DIR = "uploads"

def validate_metadata_constraints(metadata_content):
    """Validate metadata constraints before processing"""
    validation_errors = []
    
    if 'constraints' in metadata_content:
        for constraint in metadata_content['constraints']:
            constraint_class = constraint.get('constraint_class')
            params = constraint.get('constraint_parameters', {})
            
            if constraint_class == 'ScalarRange':
                # Validate required parameters exist
                required_params = ['column_name', 'low_value', 'high_value']
                for param in required_params:
                    if param not in params:
                        validation_errors.append(f"❌ ScalarRange constraint missing required parameter: {param}")
                        continue
                
                # Validate numeric values are not strings
                if isinstance(params['low_value'], str) or isinstance(params['high_value'], str):
                    validation_errors.append(
                        f"❌ ScalarRange constraint error: 'low_value' and 'high_value' must be numeric, not strings. "
                        f"Current values: low_value={params['low_value']} ({type(params['low_value']).__name__}), "
                        f"high_value={params['high_value']} ({type(params['high_value']).__name__})"
                    )
                    continue
                
                # Try converting to float to ensure they're valid numbers
                try:
                    low_value = float(params['low_value'])
                    high_value = float(params['high_value'])
                except (TypeError, ValueError):
                    validation_errors.append(
                        f"❌ ScalarRange constraint error: Invalid numeric values for boundaries"
                    )
    
    return validation_errors

st.title("Metadata Validator")

st.markdown("""
### Metadata Validation

Validate your saved metadata files:
1. Select a metadata file
2. Validate its structure
3. View validation results
4. Check data compliance
""")

# Get all JSON files from the uploads directory
json_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.json')]

# Initialize session states
if 'metadata_validated' not in st.session_state:
    st.session_state.metadata_validated = False
if 'metadata_content' not in st.session_state:
    st.session_state.metadata_content = None
if 'metadata_path' not in st.session_state:
    st.session_state.metadata_path = None
if 'selected_data_for_validation' not in st.session_state:
    st.session_state.selected_data_for_validation = None

if json_files:
    selected_metadata_file = st.selectbox(
        "Select a metadata file to validate:",
        json_files
    )
    
    if selected_metadata_file and st.button("Validate Metadata"):
        try:
            metadata_path = os.path.join(UPLOAD_DIR, selected_metadata_file)
            
            # Load metadata content first
            with open(metadata_path, 'r') as f:
                metadata_content = json.load(f)
            
            # Validate constraints
            validation_errors = validate_metadata_constraints(metadata_content)
            
            if validation_errors:
                st.error("Metadata Validation Failed")
                for error in validation_errors:
                    st.write(error)
            else:
                # If no validation errors, proceed with metadata loading
                table_name = list(metadata_content['tables'].keys())[0]
                table_metadata = metadata_content['tables'][table_name]
                
                metadata = SingleTableMetadata()
                metadata.load_from_dict(table_metadata)
                
                # Set session state
                st.session_state.metadata_validated = True
                st.session_state.metadata_content = metadata_content
                st.session_state.metadata_path = metadata_path
                
                # Display metadata content after validation
                st.markdown("### Metadata Content")
                st.json(metadata_content)
                st.success(f"✅ Metadata in '{selected_metadata_file}' is valid!")
                
        except Exception as e:
            st.error(f"Error validating metadata: {str(e)}")

    # Show metadata structure and data validation only if metadata is validated
    if st.session_state.metadata_validated:
        st.markdown("### Metadata Structure")
        metadata_content = st.session_state.metadata_content
        table_name = list(metadata_content['tables'].keys())[0]
        table_info = metadata_content['tables'][table_name]
        
        st.write(f"**Table:** {table_name}")
        
        # Show columns
        st.write("**Columns:**")
        cols = []
        for col_name, col_info in table_info['columns'].items():
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
        
        # Check for primary key in the metadata
        if 'primary_key' in table_info:
            st.write(f"**Primary Key:** {table_info['primary_key']}")

        # Data Validation Section
        st.markdown("### Validate Data Against Metadata")
        csv_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.csv')]
        
        if csv_files:
            selected_data = st.selectbox(
                "Select a dataset to validate:",
                csv_files,
                key="data_validation_select"
            )
            
            if st.button("Validate Selected Data", key="validate_data_button"):
                try:
                    # Load the data
                    data_path = os.path.join(UPLOAD_DIR, selected_data)
                    df = pd.read_csv(data_path)
                    
                    # Load metadata
                    metadata = Metadata.load_from_json(st.session_state.metadata_path)
                    table_name = list(metadata.tables.keys())[0]
                    table_metadata = metadata.tables[table_name]
                    
                    validation_errors = []
                    violation_details = []
                    
                    # Basic column and type validation
                    for col_name, col_info in table_metadata.columns.items():
                        if col_name not in df.columns:
                            validation_errors.append(f"❌ Column '{col_name}' is missing in the dataset")
                            continue
                        
                        # Check data types
                        sdtype = col_info['sdtype']
                        if sdtype == 'numerical':
                            if not pd.api.types.is_numeric_dtype(df[col_name]):
                                validation_errors.append(f"❌ Column '{col_name}' should be numerical")
                        elif sdtype == 'datetime':
                            try:
                                df[col_name] = pd.to_datetime(df[col_name])
                            except:
                                validation_errors.append(f"❌ Column '{col_name}' contains invalid datetime values")
                        elif sdtype == 'boolean':
                            if not pd.api.types.is_bool_dtype(df[col_name].dtype):
                                validation_errors.append(f"❌ Column '{col_name}' should be boolean")
                    
                    # Check constraints if present
                    metadata_content = st.session_state.metadata_content or {}
                    if 'constraints' in metadata_content:
                        for constraint in metadata_content['constraints']:
                            constraint_class = constraint['constraint_class']
                            params = constraint['constraint_parameters']
                            
                            # Validate constraint parameters before processing
                            if constraint_class == 'ScalarRange':
                                column = params.get('column_name')
                                if not column:
                                    validation_errors.append("❌ ScalarRange constraint missing column_name")
                                    continue
                                
                                # Check if column exists and is numeric
                                if column not in table_metadata.columns:
                                    validation_errors.append(f"❌ ScalarRange constraint: Column '{column}' not found")
                                    continue
                                
                                sdtype = table_metadata.columns[column]['sdtype']
                                if sdtype not in ['numerical', 'id']:
                                    validation_errors.append(
                                        f"❌ ScalarRange constraint: Column '{column}' must be numerical or id type, found {sdtype}"
                                    )
                                    continue
                                
                                # Validate boundary values
                                try:
                                    low_value = float(params.get('low_value'))
                                    high_value = float(params.get('high_value'))
                                except (TypeError, ValueError):
                                    validation_errors.append(
                                        f"❌ ScalarRange constraint: Invalid numeric values for boundaries in column '{column}'"
                                    )
                                    continue
                                
                                if low_value >= high_value:
                                    validation_errors.append(
                                        f"❌ ScalarRange constraint: Low value must be less than high value for column '{column}'"
                                    )
                                    continue
                                
                                # Now process the actual validation
                                strict_boundaries = params.get('strict_boundaries', False)
                                column_values = pd.to_numeric(df[column], errors='coerce')
                                
                                if strict_boundaries:
                                    violations = (column_values <= low_value) | (column_values >= high_value)
                                else:
                                    violations = (column_values < low_value) | (column_values > high_value)
                                
                                violation_rows = violations[violations].index.tolist()
                                if violation_rows:
                                    boundary_type = "strictly between" if strict_boundaries else "between"
                                    validation_errors.append(
                                        f"❌ ScalarRange constraint violated: {column} should be {boundary_type} {low_value} and {high_value}"
                                    )
                                    violation_details.append({
                                        'constraint': 'ScalarRange',
                                        'columns': [column],
                                        'violation_rows': violation_rows,
                                        'details': df.loc[violation_rows, [column]]
                                    })
                            
                            elif constraint_class == 'Inequality':
                                low_col = params['low_column_name']
                                high_col = params['high_column_name']
                                
                                low_values = convert_column_data(low_col)
                                high_values = convert_column_data(high_col)
                                violations = low_values >= high_values
                                
                                violation_rows = violations[violations].index.tolist()
                                if violation_rows:
                                    validation_errors.append(
                                        f"❌ Inequality constraint violated: {low_col} should be less than {high_col}"
                                    )
                                    violation_details.append({
                                        'constraint': 'Inequality',
                                        'columns': [low_col, high_col],
                                        'violation_rows': violation_rows,
                                        'details': df.loc[violation_rows, [low_col, high_col]]
                                    })
                            
                            elif constraint_class == 'Range':
                                low_col = params['low_column_name']
                                mid_col = params['middle_column_name']
                                high_col = params['high_column_name']
                                
                                # Convert all columns
                                low_values = convert_column_data(low_col)
                                mid_values = convert_column_data(mid_col)
                                high_values = convert_column_data(high_col)
                                
                                violations = (low_values >= mid_values) | (mid_values >= high_values)
                                violation_rows = violations[violations].index.tolist()
                                if violation_rows:
                                    validation_errors.append(
                                        f"❌ Range constraint violated for {low_col} ≤ {mid_col} ≤ {high_col}"
                                    )
                                    violation_details.append({
                                        'constraint': 'Range',
                                        'columns': [low_col, mid_col, high_col],
                                        'violation_rows': violation_rows,
                                        'details': df.loc[violation_rows, [low_col, mid_col, high_col]]
                                    })
                            
                            elif constraint_class == 'ScalarInequality':
                                column = params['column_name']
                                value = params['value']
                                relation = params['relation']
                                
                                column_values = convert_column_data(column)
                                value = type(column_values.iloc[0])(value) if len(column_values) > 0 else value
                                
                                if relation == '>':
                                    violations = column_values <= value
                                elif relation == '>=':
                                    violations = column_values < value
                                elif relation == '<':
                                    violations = column_values >= value
                                elif relation == '<=':
                                    violations = column_values > value
                                
                                violation_rows = violations[violations].index.tolist()
                                if violation_rows:
                                    validation_errors.append(
                                        f"❌ ScalarInequality constraint violated: {column} should be {relation} {value}"
                                    )
                                    violation_details.append({
                                        'constraint': 'ScalarInequality',
                                        'columns': [column],
                                        'violation_rows': violation_rows,
                                        'details': df.loc[violation_rows, [column]]
                                    })
                            
                            elif constraint_class == 'Positive':
                                column = params['column_name']
                                violations = df[column] <= 0
                                violation_rows = violations[violations].index.tolist()
                                if violation_rows:
                                    validation_errors.append(
                                        f"❌ Positive constraint violated: {column} should be positive"
                                    )
                                    violation_details.append({
                                        'constraint': 'Positive',
                                        'columns': [column],
                                        'violation_rows': violation_rows,
                                        'details': df.loc[violation_rows, [column]]
                                    })
                            
                            elif constraint_class == 'Negative':
                                column = params['column_name']
                                violations = df[column] >= 0
                                violation_rows = violations[violations].index.tolist()
                                if violation_rows:
                                    validation_errors.append(
                                        f"❌ Negative constraint violated: {column} should be negative"
                                    )
                                    violation_details.append({
                                        'constraint': 'Negative',
                                        'columns': [column],
                                        'violation_rows': violation_rows,
                                        'details': df.loc[violation_rows, [column]]
                                    })
                            
                            elif constraint_class == 'OneHotEncoding':
                                columns = params['column_names']
                                row_sums = df[columns].sum(axis=1)
                                violations = row_sums != 1
                                violation_rows = violations[violations].index.tolist()
                                if violation_rows:
                                    validation_errors.append(
                                        f"❌ OneHotEncoding constraint violated: Exactly one of {columns} should be 1"
                                    )
                                    violation_details.append({
                                        'constraint': 'OneHotEncoding',
                                        'columns': columns,
                                        'violation_rows': violation_rows,
                                        'details': df.loc[violation_rows, columns]
                                    })
                            
                            elif constraint_class == 'FixedIncrements':
                                column = params['column_name']
                                increment_value = params['increment_value']
                                
                                # Check if values are multiples of increment_value
                                violations = (df[column] % increment_value) != 0
                                violation_rows = violations[violations].index.tolist()
                                if violation_rows:
                                    validation_errors.append(
                                        f"❌ FixedIncrements constraint violated: {column} should be in increments of {increment_value}"
                                    )
                                    violation_details.append({
                                        'constraint': 'FixedIncrements',
                                        'columns': [column],
                                        'violation_rows': violation_rows,
                                        'details': df.loc[violation_rows, [column]]
                                    })
                            
                            elif constraint_class == 'FixedCombinations':
                                columns = params['column_names']
                                # Get unique combinations in the dataset
                                current_combinations = df[columns].drop_duplicates().values.tolist()
                                allowed_combinations = params.get('allowed_combinations', current_combinations)
                                
                                # Check for invalid combinations
                                violations = ~df[columns].apply(tuple, axis=1).isin([tuple(c) for c in allowed_combinations])
                                violation_rows = violations[violations].index.tolist()
                                if violation_rows:
                                    validation_errors.append(
                                        f"❌ FixedCombinations constraint violated: Invalid combinations found in {columns}"
                                    )
                                    violation_details.append({
                                        'constraint': 'FixedCombinations',
                                        'columns': columns,
                                        'violation_rows': violation_rows,
                                        'details': df.loc[violation_rows, columns]
                                    })
                    
                    # Display validation results
                    if validation_errors:
                        st.error("Data Validation Failed")
                        for error in validation_errors:
                            st.write(error)
                        
                        # Show violation details in expandable sections
                        if violation_details:
                            st.markdown("### Violation Details")
                            for violation in violation_details:
                                with st.expander(f"{violation['constraint']} Violation - {', '.join(violation['columns'])}"):
                                    st.write(f"Found {len(violation['violation_rows'])} violations")
                                    st.dataframe(violation['details'])
                    else:
                        st.success("✅ Data follows all metadata rules!")
                    
                except Exception as e:
                    st.error(f"Error validating data: {str(e)}")
        else:
            st.info("No CSV files found to validate. Please upload some data files first.")
else:
    st.info("No metadata files found. Please create and save metadata first in the Metadata Manager.") 