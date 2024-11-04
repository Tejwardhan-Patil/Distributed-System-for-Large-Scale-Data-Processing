import dask
from dask.distributed import Client, progress
import dask.dataframe as dd
import pandas as pd
import numpy as np
import os
import yaml
import logging

# Load Dask configuration from YAML file
def load_dask_config(config_path='compute/dask/dask_config.yaml'):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

# Initialize logging
def setup_logging(log_file='dask_processing.log'):
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Logging initialized.")

# Set up Dask client with configuration
def setup_dask_client(scheduler_address=None, n_workers=4, threads_per_worker=2, memory_limit='2GB'):
    if scheduler_address:
        client = Client(scheduler_address)
        logging.info(f"Connected to Dask scheduler at {scheduler_address}")
    else:
        client = Client(n_workers=n_workers, threads_per_worker=threads_per_worker, memory_limit=memory_limit)
        logging.info("Dask client started with local cluster")
    return client

# Load data as Dask DataFrame
def load_data(file_path, format='csv', delimiter=',', usecols=None):
    logging.info(f"Loading data from {file_path}")
    if format == 'csv':
        df = dd.read_csv(file_path, delimiter=delimiter, usecols=usecols)
    elif format == 'parquet':
        df = dd.read_parquet(file_path)
    else:
        raise ValueError("Unsupported format. Use 'csv' or 'parquet'.")
    logging.info(f"Data loaded from {file_path} with {df.npartitions} partitions")
    return df

# Clean and preprocess the data
def clean_data(df, columns_to_drop=None, missing_threshold=0.1):
    logging.info("Cleaning data")
    if columns_to_drop:
        df = df.drop(columns=columns_to_drop)
    
    # Dropping columns with too many missing values
    missing_percentages = df.isnull().mean().compute()
    cols_to_drop = missing_percentages[missing_percentages > missing_threshold].index
    df = df.drop(columns=cols_to_drop)
    logging.info(f"Dropped columns with missing data over {missing_threshold*100}% threshold: {list(cols_to_drop)}")
    return df

# Transformation: Add a computed column
def add_computed_column(df, new_column_name='computed_column', func=None):
    if func is None:
        func = lambda row: row.sum()  # Default computation: row-wise sum
    df[new_column_name] = df.apply(func, axis=1, meta=('x', 'f8'))
    logging.info(f"Added new column: {new_column_name}")
    return df

# Save the processed data
def save_data(df, output_path, format='csv'):
    logging.info(f"Saving processed data to {output_path}")
    if format == 'csv':
        df.to_csv(output_path, single_file=True)
    elif format == 'parquet':
        df.to_parquet(output_path)
    else:
        raise ValueError("Unsupported format. Use 'csv' or 'parquet'.")
    logging.info(f"Data saved to {output_path}")

# Run the distributed processing
def run_dask_processing(config_file='compute/dask/dask_config.yaml'):
    try:
        # Load configuration
        config = load_dask_config(config_file)
        
        # Set up logging
        setup_logging(config.get('log_file', 'dask_processing.log'))
        
        # Initialize Dask client
        client = setup_dask_client(
            scheduler_address=config.get('scheduler_address', None),
            n_workers=config.get('n_workers', 4),
            threads_per_worker=config.get('threads_per_worker', 2),
            memory_limit=config.get('memory_limit', '2GB')
        )
        
        # Load the data
        file_path = config['data']['file_path']
        format = config['data'].get('format', 'csv')
        delimiter = config['data'].get('delimiter', ',')
        usecols = config['data'].get('usecols', None)
        df = load_data(file_path, format=format, delimiter=delimiter, usecols=usecols)
        
        # Clean the data
        columns_to_drop = config['data'].get('columns_to_drop', None)
        missing_threshold = config['data'].get('missing_threshold', 0.1)
        df = clean_data(df, columns_to_drop=columns_to_drop, missing_threshold=missing_threshold)
        
        # Transform the data
        new_column_name = config['transformation'].get('new_column_name', 'computed_column')
        df = add_computed_column(df, new_column_name=new_column_name)
        
        # Save the processed data
        output_path = config['output']['output_path']
        output_format = config['output'].get('format', 'csv')
        save_data(df, output_path=output_path, format=output_format)
        
        # Compute and finalize the tasks
        progress(df)
        logging.info("Dask processing completed successfully.")
    except Exception as e:
        logging.error(f"Error during Dask processing: {e}")
        raise

# Custom transformation function
def custom_transformation(row):
    return row['col1'] * row['col2'] if 'col1' in row and 'col2' in row else 0

# Main entry point for Dask processing
if __name__ == "__main__":
    run_dask_processing('compute/dask/dask_config.yaml')