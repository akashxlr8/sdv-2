import streamlit as st
import pandas as pd
import os
import json
from sdv.metadata import Metadata, SingleTableMetadata
from datetime import datetime
from utils.file_naming import generate_filename

UPLOAD_DIR = "uploads"

# Define sdtype reference dictionary
sdtype_reference = {
    'numerical': 'Numbers (integers or floats) - e.g., age, price, quantity',
    'categorical': 'Discrete values from a finite set - e.g., category, status, color',
    'boolean': 'True/False values',
    'datetime': 'Date and time values - e.g., transaction_date, created_at',
    'id': 'Unique identifiers - e.g., user_id, order_number',
    'vin': 'Vehicle Identification Number - unique code for vehicle identification',
    'license_plate': 'License Plate Number - varies by country format',
    'iban': 'International Bank Account Number - standardized bank account number',
    'swift11': 'SWIFT Bank Code (11 digits) - bank identification code',
    'swift8': 'SWIFT Bank Code (8 digits) - bank identification code',
    'credit_card_number': 'Credit Card Number - digits only',
    'email': 'Email addresses',
    'name': 'Full names of people',
    'first_name': 'First names of people',
    'last_name': 'Last names of people',
    'phone_number': 'Phone numbers in various formats',
    'ssn': 'Social Security Numbers',
    'address': 'Physical addresses',
    'city': 'City names',
    'country': 'Country names',
    'country_code': 'Two-letter country codes (ISO)',
    'company': 'Company/organization names',
    'job': 'Job titles/positions',
    'ipv4': 'IPv4 addresses',
    'ipv6': 'IPv6 addresses',
    'mac_address': 'MAC addresses',
    'latitude': 'Geographical latitude coordinates',
    'longitude': 'Geographical longitude coordinates'
}

def detect_single_table_metadata(df, table_name):
    """Detect metadata for a single table using SDV"""
    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(data=df)
    return metadata

def display_column_metadata_editor(metadata, table_name, column_name, column_metadata):
    """Display editor for a single column's metadata"""
    st.markdown(f"#### {column_name}")
    
    col1, col2 = st.columns([1, 1])
    
    # Get current sdtype with fallback to 'categorical'
    current_sdtype = column_metadata.get('sdtype', 'categorical')
    
    # Updated sdtype options according to SDV documentation
    sdtype_options = [
        'numerical',
        'categorical',
        'boolean',
        'datetime',
        'id',
        'vin',
        'license_plate',
        'iban',
        'swift11',
        'swift8',
        'credit_card_number',
        'address',
        'email',
        'name',
        'phone_number',
        'ssn',
        'first_name',
        'last_name',
        'gender',
        'city',
        'country',
        'country_code',
        'company',
        'job',
        'ipv4',
        'ipv6',
        'mac_address',
        'latitude',
        'longitude'
    ]
    
    # If current_sdtype is not in our options, default to categorical
    default_index = sdtype_options.index('categorical')
    if current_sdtype in sdtype_options:
        default_index = sdtype_options.index(current_sdtype)
    
    with col1:
        sdtype = st.selectbox(
            "SDType",
            options=sdtype_options,
            key=f"{table_name}_{column_name}_sdtype",
            index=default_index
        )
    
    with col2:
        if sdtype == 'numerical':
            computer_representation = st.selectbox(
                "Computer Representation",
                options=['Int8', 'Int16', 'Int32', 'Int64', 'Float'],
                key=f"{table_name}_{column_name}_repr",
                index=['Int8', 'Int16', 'Int32', 'Int64', 'Float'].index(
                    column_metadata.get('computer_representation', 'Float')
                )
            )
            metadata.update_column(
                column_name=column_name,
                sdtype=sdtype,
                computer_representation=computer_representation
            )
        
        elif sdtype == 'datetime':
            datetime_format = st.text_input(
                "DateTime Format",
                value=column_metadata.get('datetime_format', '%Y-%m-%d'),
                key=f"{table_name}_{column_name}_format"
            )
            metadata.update_column(
                column_name=column_name,
                sdtype=sdtype,
                datetime_format=datetime_format
            )
        
        elif sdtype == 'id':
            regex_format = st.text_input(
                "Regex Format",
                value=column_metadata.get('regex_format', '[0-9]+'),
                key=f"{table_name}_{column_name}_regex"
            )
            if not regex_format:
                regex_format = '[0-9]+'
            try:
                metadata.update_column(
                    column_name=column_name,
                    sdtype=sdtype,
                    regex_format=regex_format
                )
            except Exception as e:
                st.error(f"Invalid regex format: {str(e)}")
                metadata.update_column(
                    column_name=column_name,
                    sdtype=sdtype,
                    regex_format='[0-9]+'
                )
        
        else:
            # For all other sdtypes, no additional parameters needed
            metadata.update_column(
                column_name=column_name,
                sdtype=sdtype
            )

    return metadata

def save_metadata_json(metadata, table_name, timestamp):
    """Save metadata in SDV's JSON format"""
    metadata_json = {
        "tables": {
            table_name: {
                "columns": {},
                "primary_key": None,
                "sequence_key": None,
                "alternate_keys": [],
                "semantic_types": {},
                "constraints": [],
                "dtype_format": "numpy"
            }
        },
        "relationships": [],
        "dtype_format": "numpy",
        "constraints": []
    }
    
    # Process columns using SingleTableMetadata's column properties
    for column_name, column_info in metadata.columns.items():
        column_data = {
            "sdtype": column_info['sdtype']
        }
        
        # Add additional parameters based on sdtype
        if column_info['sdtype'] == 'numerical':
            column_data["computer_representation"] = column_info.get('computer_representation', 'Float')
        elif column_info['sdtype'] == 'datetime':
            column_data["datetime_format"] = column_info.get('datetime_format', '%Y-%m-%d')
        elif column_info['sdtype'] == 'id':
            column_data["regex_format"] = column_info.get('regex_format', '[0-9]+')
            metadata_json["tables"][table_name]["primary_key"] = column_name
            
        metadata_json["tables"][table_name]["columns"][column_name] = column_data
    
    # Save metadata
    metadata_filename = f"metadata_{table_name}_{timestamp}.json"
    metadata_path = os.path.join(UPLOAD_DIR, metadata_filename)
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata_json, f, indent=4)
    
    return metadata_filename

st.title("Metadata Manager")

st.markdown("""
### Metadata Detection and Management

Select files and manage their metadata in real-time:
1. Select CSV files
2. Auto-detect metadata
3. Edit metadata properties
4. Save configuration
""")

# Add SDType Reference Guide
st.markdown("### SDType Reference Guide")

# Create a DataFrame for better display
reference_df = pd.DataFrame([
    {'SDType': sdtype, 'Description': desc}
    for sdtype, desc in sdtype_reference.items()
])

st.dataframe(reference_df, hide_index=True, use_container_width=True)

st.markdown("---")

# Create two tabs
tab1, tab2 = st.tabs(["Load Existing Metadata", "Create New Metadata"])

with tab1:
    st.markdown("### Load Existing Metadata")
    json_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.json')]
    
    if not json_files:
        st.info("No metadata files found. Use the 'Create New Metadata' tab to create one.")
    else:
        selected_metadata_file = st.selectbox(
            "Select a metadata file to load:",
            json_files
        )
        
        if selected_metadata_file and st.button("Load Metadata"):
            try:
                metadata_path = os.path.join(UPLOAD_DIR, selected_metadata_file)
                with open(metadata_path, 'r') as f:
                    metadata_content = json.load(f)
                
                st.success("Metadata loaded successfully!")
                st.json(metadata_content)
                
                # Show edit button
                if st.button("Edit This Metadata"):
                    st.session_state.metadata_dict = {}
                    table_name = list(metadata_content['tables'].keys())[0]
                    
                    # Convert JSON metadata to SingleTableMetadata
                    metadata = SingleTableMetadata()
                    table_metadata = metadata_content['tables'][table_name]
                    
                    for column_name, column_props in table_metadata['columns'].items():
                        update_args = {'sdtype': column_props['sdtype']}
                        if 'computer_representation' in column_props:
                            update_args['computer_representation'] = column_props['computer_representation']
                        if 'datetime_format' in column_props:
                            update_args['datetime_format'] = column_props['datetime_format']
                        metadata.update_column(column_name, **update_args)
                    
                    st.session_state.metadata_dict[selected_metadata_file] = metadata
                    st.session_state.constraints = metadata_content.get('constraints', [])
                    st.rerun()
                
            except Exception as e:
                st.error(f"Error loading metadata: {str(e)}")

with tab2:
    st.markdown("### Create New Metadata")
    # Existing metadata type selection and creation logic
    metadata_type = st.radio(
        "Select Metadata Type",
        ["Single Table", "Multi Table"],
        help="Choose whether to configure metadata for a single table or multiple related tables"
    )

if os.path.exists(UPLOAD_DIR):
    files = os.listdir(UPLOAD_DIR)
    csv_files = [f for f in files if f.endswith('.csv')]
    
    if not csv_files:
        st.warning("No CSV files found. Please upload CSV files first.")
    else:
        if metadata_type == "Single Table":
            # Single file selection
            selected_file = st.selectbox(
                "Select a CSV file for metadata detection:",
                csv_files
            )
            
            if selected_file:
                if 'metadata_dict' not in st.session_state:
                    st.session_state.metadata_dict = {}
                
                # Load and display data preview
                file_path = os.path.join(UPLOAD_DIR, selected_file)
                df = pd.read_csv(file_path)
                
                st.markdown("### Data Preview")
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.dataframe(
                        df.head(),
                        use_container_width=True
                    )
                
                with col2:
                    st.info(f"""
                    **File Details:**
                    - Rows: {len(df)}
                    - Columns: {len(df.columns)}
                    - Memory Usage: {df.memory_usage().sum() / 1024:.2f} KB
                    """)
                
                # Display column info
                st.markdown("### Column Information")
                column_info = pd.DataFrame({
                    'Data Type': df.dtypes,
                    'Non-Null Count': df.count(),
                    'Null Count': df.isnull().sum(),
                    'Unique Values': df.nunique()
                })
                st.dataframe(column_info, use_container_width=True)
                
                st.markdown("### Metadata Editor")
                # Auto-detect metadata for selected file
                if selected_file not in st.session_state.metadata_dict:
                    file_path = os.path.join(UPLOAD_DIR, selected_file)
                    df = pd.read_csv(file_path)
                    table_name = os.path.splitext(selected_file)[0].upper()
                    metadata = detect_single_table_metadata(df, table_name)
                    st.session_state.metadata_dict[selected_file] = metadata
                
                # Display metadata editor
                st.markdown(f"### Editing Metadata for: {selected_file}")
                metadata = st.session_state.metadata_dict[selected_file]
                
                # Display column editors
                for column_name in metadata.columns:
                    column_metadata = metadata.columns[column_name]
                    metadata = display_column_metadata_editor(
                        metadata,
                        selected_file,
                        column_name,
                        column_metadata
                    )
                    st.session_state.metadata_dict[selected_file] = metadata
                
                # Add after the column editors section, before the save button
                st.markdown("### Constraints Configuration")

                # Initialize constraints in session state if not exists
                if 'constraints' not in st.session_state:
                    st.session_state.constraints = []

                # Add new constraint section
                st.subheader("Add New Constraint")
                constraint_type = st.selectbox(
                    "Constraint Type",
                    ["ScalarRange", "OneHotEncoding", "Positive", "Negative", "Between", "UniqueCombinations"],
                    help="Select the type of constraint to add"
                )

                # Different inputs based on constraint type
                if constraint_type == "ScalarRange":
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        column = st.selectbox("Column", metadata.columns.keys())
                        column_sdtype = metadata.columns[column]['sdtype']
                    
                    with col2:
                        low_value = get_value_input_for_sdtype(
                            column_sdtype,
                            "Minimum Value",
                            f"scalar_range_low_{column}"
                        )
                    
                    with col3:
                        high_value = get_value_input_for_sdtype(
                            column_sdtype,
                            "Maximum Value",
                            f"scalar_range_high_{column}"
                        )
                    
                    strict = st.checkbox("Strict Boundaries", value=False)
                    
                    if st.button("Add ScalarRange Constraint"):
                        try:
                            # Convert values to appropriate type based on sdtype
                            if column_sdtype in ['numerical', 'id']:
                                low_value = float(low_value)
                                high_value = float(high_value)
                            
                            new_constraint = {
                                'constraint_class': 'ScalarRange',
                                'constraint_parameters': {
                                    'column_name': column,
                                    'low_value': low_value,  # Will be stored as actual number
                                    'high_value': high_value,  # Will be stored as actual number
                                    'strict_boundaries': strict
                                }
                            }
                            st.session_state.constraints.append(new_constraint)
                            st.success("Constraint added!")
                        except ValueError:
                            st.error("Invalid numeric values provided for ScalarRange constraint")

                elif constraint_type == "Positive":
                    column = st.selectbox("Column", metadata.columns.keys())
                    strict = st.checkbox("Strict (Exclude Zero)", value=False)
                    
                    if st.button("Add Positive Constraint"):
                        new_constraint = {
                            'constraint_class': 'Positive',
                            'constraint_parameters': {
                                'column_name': column,
                                'strict': strict
                            }
                        }
                        st.session_state.constraints.append(new_constraint)
                        st.success("Constraint added!")

                elif constraint_type == "Between":
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        column = st.selectbox("Column", metadata.columns.keys())
                        column_sdtype = metadata.columns[column]['sdtype']
                    
                    with col2:
                        low_value = get_value_input_for_sdtype(
                            column_sdtype,
                            "Minimum Value",
                            f"between_low_{column}"
                        )
                    
                    with col3:
                        high_value = get_value_input_for_sdtype(
                            column_sdtype,
                            "Maximum Value",
                            f"between_high_{column}"
                        )
                    
                    if st.button("Add Between Constraint"):
                        new_constraint = {
                            'constraint_class': 'Between',
                            'constraint_parameters': {
                                'column_name': column,
                                'low_value': low_value,
                                'high_value': high_value
                            }
                        }
                        st.session_state.constraints.append(new_constraint)
                        st.success("Constraint added!")

                elif constraint_type == "Inequality":
                    col1, col2 = st.columns(2)
                    with col1:
                        low_column = st.selectbox(
                            "Low Column",
                            [col for col, info in metadata.columns.items() 
                             if info['sdtype'] in ['numerical', 'datetime']],
                            help="Column with lower values"
                        )
                    
                    with col2:
                        high_column = st.selectbox(
                            "High Column",
                            [col for col, info in metadata.columns.items() 
                             if info['sdtype'] in ['numerical', 'datetime']],
                            help="Column with higher values"
                        )

                # Add after the Inequality constraint section

                elif constraint_type == "FixedIncrements":
                    col1, col2 = st.columns(2)
                    with col1:
                        column = st.selectbox(
                            "Column",
                            metadata.columns.keys(),
                            help="Select the column that must follow fixed increments"
                        )
                    with col2:
                        increment = st.number_input(
                            "Increment Value",
                            min_value=1,
                            value=1,
                            help="The size of the increment. Must be a positive integer"
                        )
                    
                    if st.button("Add FixedIncrements Constraint"):
                        new_constraint = {
                            'constraint_class': 'FixedIncrements',
                            'constraint_parameters': {
                                'column_name': column,
                                'increment': int(increment)
                            }
                        }
                        st.session_state.constraints.append(new_constraint)
                        st.success("Constraint added!")

                # Add after the FixedIncrements constraint section

                elif constraint_type == "FixedCombinations":
                    # Allow selection of multiple columns
                    selected_columns = st.multiselect(
                        "Select Columns",
                        metadata.columns.keys(),
                        help="Select two or more columns whose combinations should be fixed"
                    )
                    
                    # Only show the add button if 2 or more columns are selected
                    if len(selected_columns) >= 2:
                        if st.button("Add FixedCombinations Constraint"):
                            new_constraint = {
                                'constraint_class': 'FixedCombinations',
                                'constraint_parameters': {
                                    'column_names': selected_columns
                                }
                            }
                            st.session_state.constraints.append(new_constraint)
                            st.success("Constraint added!")
                    else:
                        st.info("Please select at least 2 columns to create a FixedCombinations constraint.")

                # Add after the FixedCombinations constraint section

                elif constraint_type == "OneHotEncoding":
                    # Allow selection of multiple columns that form the one-hot encoding
                    selected_columns = st.multiselect(
                        "Select One-Hot Encoded Columns",
                        metadata.columns.keys(),
                        help="Select columns that together form a one-hot encoding (exactly one column should be 1, others 0)"
                    )
                    
                    if len(selected_columns) >= 2:
                        if st.button("Add OneHotEncoding Constraint"):
                            new_constraint = {
                                'constraint_class': 'OneHotEncoding',
                                'constraint_parameters': {
                                    'column_names': selected_columns
                                }
                            }
                            st.session_state.constraints.append(new_constraint)
                            st.success("Constraint added!")
                    else:
                        st.info("Please select at least 2 columns to create a OneHotEncoding constraint.")

                # Display current constraints
                if st.session_state.constraints:
                    st.markdown("### Current Constraints")
                    for i, constraint in enumerate(st.session_state.constraints):
                        st.markdown(f"**{constraint['constraint_class']}**")
                        st.json(constraint['constraint_parameters'])
                        if st.button(f"Remove Constraint {i+1}"):
                            st.session_state.constraints.pop(i)
                            st.rerun()

                # Save metadata button and filename customization
                col1, col2 = st.columns([3, 1])

                with col1:
                    # Initialize the session state for filename if not exists
                    if 'custom_filename' not in st.session_state:
                        st.session_state.custom_filename = generate_filename(
                            "metadata",
                            source_files=[selected_file]
                        )
                    
                    # Use session state to persist user's input
                    custom_filename = st.text_input(
                        "Filename for metadata",
                        value=st.session_state.custom_filename,
                        help="You can modify the filename (without extension)",
                        key="metadata_filename_input"
                    ).strip()
                    
                    # Update session state when user changes the input
                    st.session_state.custom_filename = custom_filename

                with col2:
                    if st.button("Save Metadata Configuration"):
                        try:
                            if not custom_filename:
                                st.error("Filename cannot be empty")
                                st.stop()
                                
                            metadata = st.session_state.metadata_dict[selected_file]
                            table_name = os.path.splitext(selected_file)[0].upper()
                            
                            # Update the metadata_json in the save button section to include constraints
                            metadata_json = {
                                "tables": {
                                    table_name: metadata.to_dict()
                                },
                                "relationships": [],
                                "dtype_format": "numpy",
                                "constraints": st.session_state.constraints
                            }
                            
                            # Ensure .json extension
                            if not custom_filename.endswith('.json'):
                                metadata_filename = f"{custom_filename}.json"
                            else:
                                metadata_filename = custom_filename
                                
                            metadata_path = os.path.join(UPLOAD_DIR, metadata_filename)
                            
                            with open(metadata_path, 'w') as f:
                                json.dump(metadata_json, f, indent=4)
                            
                            st.success(f"Saved metadata as: {metadata_filename}")
                        except Exception as e:
                            st.error(f"Error saving metadata: {str(e)}")
        
        else:  # Multi Table
            # Multi-file selection
            selected_files = st.multiselect(
                "Select CSV files for metadata detection:",
                csv_files
            )
            
            if selected_files:
                st.markdown("### Multi-table Metadata Configuration")
                # Rest of the multi-table configuration code...
                
else:
    st.warning("Upload directory does not exist. Please upload files first.")