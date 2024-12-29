import streamlit as st
import pandas as pd
import os
import json
from sdv.metadata import Metadata, SingleTableMetadata
from datetime import datetime
from utils.file_naming import generate_filename

UPLOAD_DIR = "uploads"

def detect_metadata(file_path):
    """Detect metadata from a CSV file using SDV's SingleTableMetadata."""
    df = pd.read_csv(os.path.join(UPLOAD_DIR, file_path))
    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(df)
    return metadata

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

def display_table_settings(metadata):
    """Display table-level settings like primary key"""
    st.markdown("### Table Settings")
    
    # Primary Key Selection
    primary_key = st.selectbox(
        "Primary Key",
        options=["None"] + list(metadata.columns.keys()),
        index=0 if metadata.primary_key is None else list(metadata.columns.keys()).index(metadata.primary_key) + 1,
        help="Select the primary key column (must contain unique values)"
    )
    
    if primary_key != "None":
        metadata.set_primary_key(primary_key)
    else:
        metadata.set_primary_key(None)

def detect_single_table_metadata(df, table_name):
    """Detect metadata for a single table using SDV"""
    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(df)
    return metadata

def display_column_metadata_editor(metadata, table_name, column_name, column_metadata):
    """Display editor for a single column's metadata"""
    st.markdown(f"#### {column_name}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        current_sdtype = column_metadata.get('sdtype', 'categorical')
        if current_sdtype not in sdtype_reference:
            current_sdtype = 'categorical'
            
        sdtype = st.selectbox(
            "SDType",
            options=list(sdtype_reference.keys()),
            key=f"sdtype_{table_name}_{column_name}",
            index=list(sdtype_reference.keys()).index(current_sdtype)
        )
    
    with col2:
        if sdtype == 'numerical':
            computer_representation = st.selectbox(
                "Computer Representation",
                ["Int64", "Int32", "Int16", "Int8", "Float"],
                key=f"comp_rep_{table_name}_{column_name}",
                index=["Int64", "Int32", "Int16", "Int8", "Float"].index(
                    column_metadata.get('computer_representation', 'Float')
                )
            )
            metadata.update_column(
                column_name=column_name,
                sdtype=sdtype,
                computer_representation=computer_representation
            )
        elif sdtype == 'id':
            regex_format = st.text_input(
                "Regex Format",
                value=column_metadata.get('regex_format', '[0-9]+'),
                help="Regular expression pattern for ID generation",
                key=f"{table_name}_{column_name}_regex"
            )
            metadata.update_column(
                column_name=column_name,
                sdtype=sdtype,
                regex_format=regex_format
            )
        elif sdtype == 'datetime':
            st.info("""
            Common datetime format codes:
            - %Y: Year with century (2024)
            - %m: Month as zero-padded number (01-12)
            - %d: Day of the month as zero-padded number (01-31)
            - %H: Hour (24-hour clock) as zero-padded number (00-23)
            - %M: Minute as zero-padded number (00-59)
            - %S: Second as zero-padded number (00-59)
            
            Examples:
            - %Y-%m-%d = 2024-03-15
            - %Y-%m-%d %H:%M:%S = 2024-03-15 14:30:00
            - %d/%m/%Y = 15/03/2024
            """)
            
            datetime_format = st.text_input(
                "DateTime Format",
                value=column_metadata.get('datetime_format', '%Y-%m-%d %H:%M:%S'),
                key=f"{table_name}_{column_name}_format",
                help="Enter the format that matches your data"
            )
            metadata.update_column(
                column_name=column_name,
                sdtype=sdtype,
                datetime_format=datetime_format
            )
        else:
            metadata.update_column(
                column_name=column_name,
                sdtype=sdtype
            )
    
    return metadata

def save_metadata_json(metadata, table_name, timestamp):
    metadata_json = {
        "tables": {
            table_name: {
                "columns": {},
                "primary_key": metadata.primary_key,
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
    
    # Process columns
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
            
        metadata_json["tables"][table_name]["columns"][column_name] = column_data
    
    # Save metadata
    metadata_filename = f"metadata_{table_name}_{timestamp}.json"
    metadata_path = os.path.join(UPLOAD_DIR, metadata_filename)
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata_json, f, indent=4)
    
    return metadata_filename



def get_value_input_for_sdtype(sdtype, label, key):
    """Get appropriate input widget based on column sdtype"""
    if sdtype == 'datetime':
        value = st.date_input(
            label,
            help="Select the date",
            key=key
        )
        # Handle both single date and date range returns
        if isinstance(value, tuple):
            if len(value) > 0:
                return value[0].strftime('%Y-%m-%d')
            return datetime.today().strftime('%Y-%m-%d')  # fallback to today's date
        return value.strftime('%Y-%m-%d') if value else datetime.today().strftime('%Y-%m-%d')  # handle None
    elif sdtype in ['numerical', 'id']:
        return float(st.number_input(
            label,
            value=0,
            key=key
        ))
    else:
        return st.text_input(label, key=key)

def load_metadata_from_json(json_path):
    """Load metadata from JSON file and create SingleTableMetadata instance"""
    with open(json_path, 'r') as f:
        metadata_json = json.load(f)
    
    table_name = list(metadata_json['tables'].keys())[0]
    table_info = metadata_json['tables'][table_name]
    
    metadata = SingleTableMetadata()
    
    # Load columns with their properties
    for col_name, col_info in table_info['columns'].items():
        update_args = {'sdtype': col_info['sdtype']}
        
        # Add additional properties based on sdtype
        if col_info['sdtype'] == 'numerical' and 'computer_representation' in col_info:
            update_args['computer_representation'] = col_info['computer_representation']
        elif col_info['sdtype'] == 'datetime' and 'datetime_format' in col_info:
            update_args['datetime_format'] = col_info['datetime_format']
        elif col_info['sdtype'] == 'id' and 'regex_format' in col_info:
            update_args['regex_format'] = col_info['regex_format']
        
        metadata.update_column(col_name, **update_args)
    
    # Load constraints if they exist
    if 'constraints' in metadata_json:
        st.session_state.constraints = metadata_json['constraints']
    
    return metadata, table_name

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
        st.info("No metadata files found. Use the 'Create New Metadata' tab to create one and manage them in the File Manager.")
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
                
                # Show metadata content in an expander
                with st.expander("View Raw Metadata"):
                    st.json(metadata_content)
                
                # Load existing constraints
                st.session_state.constraints = metadata_content.get('constraints', [])
                
                # Display and edit existing constraints
                if st.session_state.constraints:
                    st.markdown("### Existing Constraints")
                    for i, constraint in enumerate(st.session_state.constraints):
                        with st.expander(f"Constraint {i+1}: {constraint['constraint_class']}"):
                            # Display current parameters
                            st.json(constraint['constraint_parameters'])
                            
                            # Add edit functionality based on constraint type
                            if constraint['constraint_class'] == 'ScalarRange':
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    # Get table name from metadata content
                                    table_name = list(metadata_content['tables'].keys())[0]
                                    metadata = Metadata()
                                    metadata.load_from_dict(metadata_content['tables'][table_name])
                                    column = st.selectbox(
                                        "Column", 
                                        metadata.columns.keys(),
                                        key=f"edit_scalar_col_{i}",
                                        index=0  # Default to first column if previous column not found
                                    )
                                with col2:
                                    low_value = st.number_input(
                                        "Minimum Value", 
                                        value=constraint['constraint_parameters']['low_value'],
                                        key=f"edit_scalar_low_{i}"
                                    )
                                with col3:
                                    high_value = st.number_input(
                                        "Maximum Value", 
                                        value=constraint['constraint_parameters']['high_value'],
                                        key=f"edit_scalar_high_{i}"
                                    )
                                strict = st.checkbox(
                                    "Strict Boundaries", 
                                    value=constraint['constraint_parameters']['strict_boundaries'],
                                    key=f"edit_scalar_strict_{i}"
                                )
                                
                                if st.button("Update Constraint", key=f"update_{i}"):
                                    st.session_state.constraints[i] = {
                                        'constraint_class': 'ScalarRange',
                                        'constraint_parameters': {
                                            'column_name': column,
                                            'low_value': low_value,
                                            'high_value': high_value,
                                            'strict_boundaries': strict
                                        }
                                    }
                                    st.success("Constraint updated!")
                                    st.rerun()
                            
                            # Add remove button
                            if st.button(f"Remove Constraint", key=f"remove_{i}"):
                                st.session_state.constraints.pop(i)
                                st.success("Constraint removed!")
                                st.rerun()
                
                # Show edit button for metadata
                if st.button("Edit This Metadata"):
                    st.session_state.metadata_dict = {}
                    table_name = list(metadata_content['tables'].keys())[0]
                    
                    # Convert JSON metadata to SingleTableMetadata
                    metadata = Metadata()
                    table_metadata = metadata_content['tables'][table_name]
                    
                    for column_name, column_props in table_metadata['columns'].items():
                        update_args = {'sdtype': column_props['sdtype']}
                        if 'computer_representation' in column_props:
                            update_args['computer_representation'] = column_props['computer_representation']
                        if 'datetime_format' in column_props:
                            update_args['datetime_format'] = column_props['datetime_format']
                        metadata.update_column(column_name, **update_args)
                    
                    st.session_state.metadata_dict[selected_metadata_file] = metadata
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
                    # Check if metadata JSON exists for this file
                    metadata_json_path = os.path.join(UPLOAD_DIR, f"metadata_{os.path.splitext(selected_file)[0]}.json")
                    if os.path.exists(metadata_json_path):
                        metadata = load_metadata_from_json(metadata_json_path)
                    else:
                        metadata = detect_metadata(selected_file)
                    st.session_state.metadata_dict[selected_file] = metadata
                
                # Display metadata editor
                st.markdown(f"### Editing Metadata for: {selected_file}")
                metadata = st.session_state.metadata_dict[selected_file]
                table_name = os.path.splitext(selected_file)[0].upper()
                
                # Display column editors
                for column_name, column_metadata in metadata.columns.items():
                    metadata = display_column_metadata_editor(
                        metadata, 
                        table_name,
                        column_name, 
                        column_metadata
                    )
                
                # Display table settings (including primary key)
                display_table_settings(metadata)
                
                # Constraints section follows...

                # Add after the column editors section, before the save button
                st.markdown("### Constraints Configuration")

                # Initialize constraints in session state if not exists
                if 'constraints' not in st.session_state:
                    st.session_state.constraints = []

                # Add new constraint section
                st.subheader("Add New Constraint")
                constraint_type = st.selectbox(
                    "Constraint Type",
                    [
                        "ScalarRange",
                        "ScalarInequality",
                        "Positive",
                        "Negative",
                        "Between",
                        "OneHotEncoding",
                        "Inequality",
                        "FixedIncrements",
                        "FixedCombinations",
                        "Range",
                        "CustomLogic"
                    ],
                    help="Select the type of constraint to add"
                )

                # Add ScalarInequality constraint section
                if constraint_type == "ScalarInequality":
                    col1, col2 = st.columns(2)
                    with col1:
                        column = st.selectbox("Column", metadata.columns.keys())
                    with col2:
                        relation = st.selectbox(
                            "Relation",
                            [">", ">=", "<", "<="],
                            help="Select the inequality relation"
                        )
                    
                    # Check column type and show appropriate input
                    column_sdtype = metadata.columns[column]['sdtype']
                    if column_sdtype == 'datetime':
                        value = st.date_input(
                            "Date Value",
                            help="Select the date to compare against"
                        )
                        # Handle tuple and None cases
                        if isinstance(value, tuple):
                            value = value[0].strftime('%Y-%m-%d') if len(value) > 0 else datetime.today().strftime('%Y-%m-%d')
                        else:
                            value = value.strftime('%Y-%m-%d') if value else datetime.today().strftime('%Y-%m-%d')
                    else:
                        value = st.number_input("Value", value=0)
                    
                    if st.button("Add ScalarInequality Constraint"):
                        new_constraint = {
                            'constraint_class': 'ScalarInequality',
                            'constraint_parameters': {
                                'column_name': column,
                                'relation': relation,
                                'value': value
                            }
                        }
                        st.session_state.constraints.append(new_constraint)
                        st.success("Constraint added!")

                # Custom Logic section
                if constraint_type == "CustomLogic":
                    st.markdown("""
                    ### Custom Logic Configuration
                    Define relationships between columns using custom logic.
                    """)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        source_column = st.selectbox("Source Column", metadata.columns.keys())
                    with col2:
                        target_column = st.selectbox("Target Column", metadata.columns.keys())
                    
                    transform_function = st.text_area(
                        "Python Transform Function",
                        value="""def transform(source_value):
    # Example: Convert full name to user ID
    words = source_value.split()
    return ''.join(word[:2].upper() for word in words)""",
                        help="Define a Python function that transforms the source column value to the target column value"
                    )
                    
                    if st.button("Add Custom Logic Constraint"):
                        new_constraint = {
                            'constraint_class': 'CustomLogic',
                            'constraint_parameters': {
                                'source_column': source_column,
                                'target_column': target_column,
                                'transform_function': transform_function
                            }
                        }
                        st.session_state.constraints.append(new_constraint)
                        st.success("Custom Logic Constraint added!")

                # Different inputs based on constraint type
                if constraint_type == "ScalarRange":
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        column = st.selectbox("Column", metadata.columns.keys())
                        column_sdtype = metadata.columns[column]['sdtype']
                    
                    with col2:
                        if column_sdtype == 'datetime':
                            # Get the datetime format from column metadata
                            datetime_format = metadata.columns[column].get('datetime_format', '%Y-%m-%d %H:%M:%S')
                            
                            # Only set default if session state doesn't exist
                            if f"scalar_range_low_{column}" not in st.session_state:
                                default_low = datetime.now().replace(year=2020, month=1, day=1).strftime(datetime_format)
                                st.session_state[f"scalar_range_low_{column}"] = default_low
                            
                            low_value = st.text_input(
                                "Minimum Date",
                                key=f"scalar_range_low_{column}",
                                help=f"Enter date in format: {datetime_format}"
                            )
                            st.caption(f"Using format: {datetime_format}")
                        else:
                            low_value = get_value_input_for_sdtype(
                                column_sdtype,
                                "Minimum Value",
                                f"scalar_range_low_{column}"
                            )
                    
                    with col3:
                        if column_sdtype == 'datetime':
                            # Default value only if no user input exists
                            default_high = datetime.now().replace(year=2023, month=12, day=31).strftime(datetime_format)
                            if f"scalar_range_high_{column}" not in st.session_state:
                                st.session_state[f"scalar_range_high_{column}"] = default_high
                            
                            high_value = st.text_input(
                                "Maximum Date",
                                value=st.session_state[f"scalar_range_high_{column}"],
                                key=f"scalar_range_high_{column}",
                                help=f"Enter date in format: {datetime_format}"
                            )
                        else:
                            high_value = get_value_input_for_sdtype(
                                column_sdtype,
                                "Maximum Value",
                                f"scalar_range_high_{column}"
                            )
                    
                    strict = st.checkbox("Strict Boundaries", value=False)
                    
                    if st.button("Add ScalarRange Constraint"):
                        try:
                            if column_sdtype == 'datetime':
                                # Validate dates match the column's format
                                datetime_format = metadata.columns[column].get('datetime_format', '%Y-%m-%d %H:%M:%S')
                                datetime.strptime(low_value, datetime_format)
                                datetime.strptime(high_value, datetime_format)
                            else:
                                if column_sdtype in ['numerical', 'id']:
                                    low_value = float(low_value)
                                    high_value = float(high_value)
                            
                            new_constraint = {
                                'constraint_class': 'ScalarRange',
                                'constraint_parameters': {
                                    'column_name': column,
                                    'low_value': low_value,
                                    'high_value': high_value,
                                    'strict_boundaries': strict
                                }
                            }
                            st.session_state.constraints.append(new_constraint)
                            st.success("Constraint added!")
                        except ValueError as e:
                            st.error(f"Invalid date format. Please use: {datetime_format}")

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