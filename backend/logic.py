from sdv.io.local import CSVHandler
from sdv.metadata import Metadata
from sdv.constraints import ScalarRange
from sdv.multi_table import HMASynthesizer
from datetime import datetime
import os
import pandas as pd
import streamlit as st
def load_csv_data(folder_name='data/'):
    """
    Load CSV files from the specified folder
    """
    try:
        connector = CSVHandler()
        print("\n--Loaded CSVs---\n")
        return connector.read(folder_name)
    except Exception as e:
        print(f"Error loading CSV data: {str(e)}")
        raise

def create_scalar_range_constraints():
    """
    Define ScalarRange constraints for both tables
    """
    return [
        # PAYMENT table constraints
        # {
        #     'constraint_class': 'ScalarRange',
        #     'table_name': 'PAYMENT',
        #     'constraint_parameters': {
        #         'column_name': 'userId',
        #         'low_value': 100001,
        #         'high_value': 999999,
        #         'strict_boundaries': False
        #     }
        # },
        {
            'constraint_class': 'ScalarRange',
            'table_name': 'PAYMENT',
            'constraint_parameters': {
                'column_name': 'paymentDate',
                'low_value': '2020-01-01',
                'high_value': '2023-12-31',
                'strict_boundaries': False
            }
        },
        # PRODUCT table constraints
        {
            'constraint_class': 'ScalarRange',
            'table_name': 'PRODUCT',
            'constraint_parameters': {
                'column_name': 'created_at',
                'low_value': '2020-01-01',
                'high_value': '2023-12-31',
                'strict_boundaries': False
            }
        }
    ]

def setup_metadata(data):
    """
    Create and configure metadata with tables and relationships
    """
    try:
        metadata = Metadata.detect_from_dataframes(data)
        print('Auto detected data:\n')
         # Update PAYMENT table column types
        metadata.update_column(table_name='PAYMENT', column_name='paymentId', sdtype='id')
        metadata.update_column(table_name='PAYMENT', column_name='invoiceId', sdtype='id')
        metadata.update_column(table_name='PAYMENT', column_name='userId', sdtype='numerical', computer_representation='Int64')
        metadata.update_column(table_name='PAYMENT', column_name='product_id', sdtype='id')
        metadata.update_column(table_name='PAYMENT', column_name='paymentDate', sdtype='datetime', datetime_format='%Y-%m-%d')
        metadata.update_column(table_name='PAYMENT', column_name='amount', sdtype='numerical', computer_representation='Float')
        metadata.update_column(table_name='PAYMENT', column_name='status', sdtype='categorical')
        metadata.update_column(table_name='PAYMENT', column_name='payment_method', sdtype='categorical')
        metadata.update_column(table_name='PAYMENT', column_name='card_number', sdtype='credit_card_number')
        metadata.update_column(table_name='PAYMENT', column_name='card_variant', sdtype='categorical')
        metadata.update_column(table_name='PAYMENT', column_name='bank_account_number', sdtype='categorical')
        metadata.update_column(table_name='PAYMENT', column_name='paypal_account', sdtype='email')
        metadata.update_column(table_name='PAYMENT', column_name='firstName', sdtype='first_name')
        metadata.update_column(table_name='PAYMENT', column_name='lastName', sdtype='last_name')
        metadata.update_column(table_name='PAYMENT', column_name='created_at', sdtype='datetime', datetime_format='%Y-%m-%d')
        metadata.update_column(table_name='PAYMENT', column_name='updated_at', sdtype='datetime', datetime_format='%Y-%m-%d')
        metadata.update_column(table_name='PAYMENT', column_name='refund_reason', sdtype='categorical')
        
        # Update PRODUCT table column types
        metadata.update_column(table_name='PRODUCT', column_name='product_id', sdtype='id')
        metadata.update_column(table_name='PRODUCT', column_name='name', sdtype='categorical')
        metadata.update_column(table_name='PRODUCT', column_name='description', sdtype='categorical')
        metadata.update_column(table_name='PRODUCT', column_name='price', sdtype='numerical', computer_representation='Float')
        metadata.update_column(table_name='PRODUCT', column_name='category', sdtype='categorical')
        metadata.update_column(table_name='PRODUCT', column_name='stock_quantity', sdtype='numerical', computer_representation='Int64')
        metadata.update_column(table_name='PRODUCT', column_name='created_at', sdtype='datetime', datetime_format='%Y-%m-%d')
        metadata.update_column(table_name='PRODUCT', column_name='updated_at', sdtype='datetime', datetime_format='%Y-%m-%d')

        print("\n---Updated metadata---\n")
        # metadata.visualize()   
        save_metadata(metadata) 
        print(metadata)        
        return metadata
        
    except Exception as e:
        print(f"Error in metadata setup: {str(e)}")
        print("Falling back to manual metadata configuration...")
        
        # Manual metadata configuration
        metadata = Metadata()
        
        # Add tables to metadata
        metadata.add_table(
            name='PAYMENT',
            data=data['PAYMENT'],
            primary_key='paymentId'
        )

        metadata.add_table(
            name='PRODUCT',
            data=data['PRODUCT'],
            primary_key='product_id'
        )

        # Add relationship between tables
        metadata.add_relationship(
            parent_table_name='PRODUCT',
            child_table_name='PAYMENT',
            parent_primary_key='product_id',
            child_foreign_key='product_id'
        )
        
        print("Manual metadata configuration completed.")
        metadata.visualize()
        return metadata

def data_validator(data):
    """
    Validate data for date consistency
    """
    try:
        violations = []
        for table_name, df in data.items():
            date_columns = df.select_dtypes(include=['datetime64']).columns
            for date_col in date_columns:
                if pd.to_datetime(df[date_col], errors='coerce').isnull().any():
                    violations.append(f"Invalid dates found in {table_name}.{date_col}")
        return violations
    except Exception as e:
        print(f"Error in data validation: {str(e)}")
        return []

def create_synthesizer(metadata, constraints):
    """
    Create and fit the synthesizer with metadata and constraints
    """
    synthesizer = HMASynthesizer(
        metadata
    )
    synthesizer.add_constraints(constraints=constraints)
    return synthesizer

def save_metadata(metadata, base_filename='metadata_with_range_constraints.json'):
    """
    Save metadata to a JSON file with a unique filename if it already exists.
    """
    # Initialize the version number
    version = 1
    filename = base_filename

    # Check if the file already exists and increment the version number
    while os.path.exists(filename):
        # Create a new filename with the version number
        filename = f"{base_filename[:-5]}_v{version}.json"  # Remove .json and add version
        version += 1

    # Save the metadata to the new filename
    try:
        metadata.save_to_json(filename)
        print(f"\nMetadata saved to '{filename}'")
    except Exception as e:
        print(f"Error saving metadata: {str(e)}")
        raise

def main():
    """
    Main function to orchestrate the data synthesis process
    """
    # Load data
    data = load_csv_data()
    
    # Create constraints
    constraints = create_scalar_range_constraints()
    
    # Setup metadata
    metadata = setup_metadata(data)
    
    # Create and configure synthesizer
    synthesizer = create_synthesizer(metadata, constraints)
    
    # Fit the synthesizer
    synthesizer.fit(data)
    
    # Print metadata summary
    print("\nMetadata with ScalarRange constraints:")
    print("====================================")
    print(metadata)
    
    # Save metadata
    save_metadata(metadata)

if __name__ == "__main__":
    main()

